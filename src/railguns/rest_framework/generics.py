"""资源接口: 增, 查, 改.

五个类, 每个类对应固定的几条路由, 没有别的写法: CreateAPI, ListAPI, ListCreateAPI, RetrieveAPI, RetrieveUpdateAPI.

    @api.viewset("/articles", auth=AUTH, guards=[AllowAny()], tags=["articles"])
    class ArticleList(ListCreateAPI):
        model = Article
        serializer_class = ArticleSerializer   # 响应, Pydantic 模型
        input_class = ArticleInput             # 请求体, Pydantic 模型. 有写入动作的类必须声明
        filterset_fields = ("score",)

约定:

- 读 (列表, 详情) 不经过 ORM 的线程池: 查询由 Django 编译成 SQL, 交给原生异步连接执行.
  编译好的 SQL 按请求的输入记下来, 同样的请求不再编译 (见 Statements).
- 更新用 ORM, 这样模型上的默认值, 信号, save() 都照常生效.
  创建的 INSERT 由 Django 编译 (pre_save, 默认值, db_default 照旧), RETURNING 响应要的列, 原生连接执行,
  一次往返. 模型有 pre_save / post_save 的接收者, 覆盖了 save(), 或者视图覆盖了创建的方法时
  走 ORM (见 API.native_create).
- 响应里只有 serializer_class 声明的字段, 每个都是列或计算字段 (见 Shape). 模型之间不用外键, 没有关联.
  请求体里只有 input_class 声明的字段能写进模型,
  主键和所有者字段不允许出现在 input_class 里, 所以请求体改不了它们.
- 写入默认要求登录, 在 Rust 里拦截, 未登录的请求不进 Python.
- 创建支持 Idempotency-Key: 带同一个键重试, 只创建一次 (见 idempotency).
"""

import re
from collections import OrderedDict
from inspect import Parameter, Signature
from threading import Lock
from typing import Any, ClassVar, Literal, TypedDict, cast, get_args
lazy import builtins
lazy from collections.abc import Awaitable, Callable
lazy from typing import LiteralString

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured, ValidationError
from django.db import IntegrityError, connections, router
from django.db.models import BigIntegerField, F, IntegerField, Lookup, Manager, Model, QuerySet, UniqueConstraint
from django.db.models.expressions import DatabaseDefault, RawSQL, Value
from django.db.models.signals import post_save, pre_save
from django.db.models.sql import InsertQuery
from django.utils import timezone
from django_filters.filterset import FilterSet, filterset_factory
from freeman.auth import IsAuthenticated
from freeman.exceptions import HTTPException
from freeman.postgres import connection
from freeman.responses import Response
from psycopg import IntegrityError as DriverIntegrityError
from pydantic import BaseModel, TypeAdapter, create_model
from pydantic.fields import FieldInfo
lazy from django.contrib.auth.base_user import AbstractBaseUser
lazy from django.db.backends.base.base import BaseDatabaseWrapper
lazy from django.db.models.fields import Field
lazy from django.db.models.sql.compiler import SQLCompiler
lazy from freeman import BoltAPI
lazy from freeman.request import Request

from railguns.django.db._introspect import default_manager, options

from . import idempotency, pagination
from .actions import http_error
from .errors import Conflict, report
from .pagination import Page, Pagination, invalid_page
from .permissions import get_user_id

PAGE_SIZE, MAX_PAGE_SIZE = pagination.PAGE_SIZE, pagination.MAX_PAGE_SIZE  # 移到了 pagination, 这里仍可导入
OWNER_FIELDS = ("user_id", "username", "user_avatar")
WRITE_ACTIONS = ("create", "update", "partial_update")
BODY_ACTIONS = ("create", "update", "partial_update")  # 有请求体的动作
# 动作 -> (请求方法, 是否作用于单个对象)
ACTIONS = {
    "list": ("get", False),
    "create": ("post", False),
    "retrieve": ("get", True),
    "update": ("put", True),
    "partial_update": ("patch", True),
}
PAGES: dict[str, type[BaseModel]] = {}  # 每个响应模型一个分页类型
FILTERSETS: dict[type, type[FilterSet] | None] = {}  # 每个视图类的 filterset 类
ENCODERS: dict[tuple[type, Any], TypeAdapter | None] = {}  # (视图类, 分页类型或 None) -> 直接编码的 TypeAdapter 或 None
SHAPES: dict[type, Shape] = {}  # 每个视图类: serializer_class 的字段怎么读
PURE: dict[type, bool] = {}  # 每个视图类: 读查询是不是只由请求的输入决定
NATIVE_CREATE: dict[type, bool] = {}  # 每个视图类: 创建能不能不经过 ORM (信号另外每次看)
SAVE_METHODS = ("save", "asave", "save_base", "_save_table", "_save_parents", "_do_insert")
TOTAL = "railguns_total"  # 一页的查询里, 总数这一列的名字

type Statement = tuple[str, str, tuple]  # 编译好的查询: (数据库别名, SQL, 参数)


class Statements:
    """编译好的读查询, 有上限的 LRU. 编译是读请求里最大的 CPU 开销, 比执行查询还贵.

    只做精确匹配: 键是查询所依赖的全部输入 (见 API.statement_key). 每个工作线程一个事件循环,
    这个表是进程里共用的, 所以加锁.
    """

    def __init__(self, maxsize: int) -> None:
        """最多记 maxsize 条."""
        self.maxsize = maxsize
        self.entries: OrderedDict[tuple, Statement] = OrderedDict()
        self.lock = Lock()

    def get(self, key: tuple) -> Statement | None:
        with self.lock:
            found = self.entries.get(key)
            if found is not None:
                self.entries.move_to_end(key)
            return found

    def put(self, key: tuple, statement: Statement) -> None:
        with self.lock:
            self.entries[key] = statement
            self.entries.move_to_end(key)
            if len(self.entries) > self.maxsize:
                self.entries.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.entries.clear()

    def __len__(self) -> int:
        """记下的条数.

        Returns:
            条数.

        """
        return len(self.entries)


STATEMENTS = Statements(4096)


def compile_statement(queryset: QuerySet) -> Statement:
    sql, params = queryset.query.sql_with_params()
    return queryset.db, sql, params


def page_statement(queryset: QuerySet, names: list[str], size: int, number: int) -> Statement:
    """第 number 页的查询. 总数作为标量子查询放在每一行的末尾, 一条语句, 一次往返.

    总数单独数主键, 不用窗口函数 count(*) OVER (): 实测它要先取出所有行的全部列再截取, 慢三倍.
    子查询放在这一页的查询里面, 而不是在外面再包一层, 这样 ORDER BY 仍然在最外层, 行的顺序有保证.

    Returns:
        这一页的查询.

    """
    count_sql, count_params = queryset.order_by().values("pk").query.sql_with_params()
    # SQL 是 Django 编译的, 值都在参数里
    total = RawSQL(f"SELECT count(*) FROM ({count_sql}) AS matched", count_params, output_field=BigIntegerField())
    return compile_statement(queryset[(number - 1) * size : number * size].values(*names, **{TOTAL: total}))


def names_model(annotation: object) -> bool:
    """类型里有没有 Pydantic 模型. 有的话那个字段的值要先建成实例才能编码.

    Returns:
        有没有.

    """
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return True
    return any(names_model(arg) for arg in get_args(annotation))


async def execute(statement: Statement) -> list[tuple]:
    """执行编译好的查询. Django 只负责编译, 执行走原生异步连接.

    Returns:
        所有的行.

    """
    alias, sql, params = statement
    async with connection(alias) as conn:
        cursor = await conn.execute(cast("LiteralString", sql), params)  # Django 编译的 SQL, 值都在参数里
        return await cursor.fetchall()


async def fetch(queryset: QuerySet, names: list[str]) -> list[dict[str, Any]]:
    """读出 queryset 的 names 这几列.

    Returns:
        每行一个字典.

    """
    rows = await execute(compile_statement(queryset.values(*names)))
    return [dict(zip(names, row, strict=True)) for row in rows]


def owner_pk(user_id: str) -> object:
    """令牌里的用户 id 转成用户表主键的类型. 转不了的 id 不是任何用户.

    Returns:
        用户表主键的值.

    Raises:
        not_a_user: 转不了的 id, 401.

    """
    try:
        return get_user_model()._meta.pk.to_python(user_id)
    except ValidationError as exc:
        raise not_a_user() from exc


def not_a_user() -> HTTPException:
    """令牌有效, 但用户已删除或停用.

    Returns:
        401 的异常.

    """
    return HTTPException(status_code=401, detail={"code": "not_authenticated", "detail": "用户不存在或已停用。"})


UNIQUE: dict[tuple[type, str], dict[str, list[str]]] = {}  # (模型, 数据库别名) -> 唯一约束名 -> 字段名


def unique_constraints(model: type[Model], alias: str) -> dict[str, list[str]]:
    """模型的唯一约束名 -> 字段名: 主键, unique=True 的字段, unique_together, 带 fields 的 UniqueConstraint.

    名字和建表时一样算: 写在列上的 UNIQUE 由 PostgreSQL 命名 (表_列_key), 其余由 Django 命名.
    超过 63 个字符时 PostgreSQL 截断, 也一并记下. 按表达式的 UniqueConstraint 没有字段.

    Returns:
        约束名 -> 字段名.

    """
    if (model, alias) in UNIQUE:
        return UNIQUE[model, alias]
    opts = options(model)
    connection = connections[alias]
    editor = connection.SchemaEditorClass(connection)
    table, found = opts.db_table, {}
    for field in opts.local_concrete_fields:
        if field.primary_key:
            found[f"{table}_pkey"] = [field.name]
        elif field.unique:
            django_name = editor._create_index_name(table, [field.column], suffix="_uniq")
            for name in (f"{table}_{field.column}_key", django_name):
                found[name] = [field.name]
    for names in opts.unique_together:
        columns = [opts.get_field(name).column for name in names]
        found[editor._create_index_name(table, columns, suffix="_uniq")] = list(names)
    for constraint in opts.constraints:
        if isinstance(constraint, UniqueConstraint):
            found[constraint.name] = list(constraint.fields)
    found |= {name[: connection.ops.max_name_length()]: fields for name, fields in found.items()}
    UNIQUE[model, alias] = found
    return found


def conflict(model: type[Model], exc: IntegrityError) -> HTTPException | None:
    """违反唯一约束 (SQLSTATE 23505) 是 409, code 是 conflict, 认得出约束时 fields 里是它的字段.

    其他完整性错误 (非空, 检查约束等) 返回 None, 照旧抛出.

    Returns:
        409 的异常, 或者 None.

    """
    cause = exc.__cause__
    if getattr(cause, "sqlstate", None) != "23505":
        return None
    constraint = cause.diag.constraint_name
    fields = unique_constraints(model, router.db_for_write(model)).get(constraint or "", [])
    errors = [{"loc": [name], "msg": "这个值已经存在。", "type": "unique"} for name in fields]
    return http_error(Conflict("已经存在相同的记录。", fields=errors))


class Links:
    """查询里 "这几个值" 的占位. 编译出来是一个参数, 执行时换成真正的值 (一个数组), 见 AnyOf 和 bind."""

    def __deepcopy__(self, memo: dict[int, object]) -> Links:
        """不复制: 编译时要认出的是这一个对象.

        Returns:
            自己.

        """
        return self


LINKS = Links()


class AnyOf(Lookup):
    """column = ANY(%s). 不管有几个值都只占一个参数, 所以查询编译一次, 之后只换参数.

    IN (%s, %s, ...) 的参数个数随值的个数变, 每次都要重新编译. 编译比执行还贵, 见 Statements.
    """

    lookup_name = "railguns_any"
    prepare_rhs = False

    def as_sql(self, compiler: SQLCompiler, connection: BaseDatabaseWrapper) -> tuple[str, tuple]:
        lhs, params = self.process_lhs(compiler, connection)
        return f"{lhs} = ANY(%s)", (*params, self.rhs)


def bind(statement: Statement, links: list) -> Statement:
    """编译好的查询里的 LINKS 换成这次的值.

    Returns:
        换好参数的查询.

    """
    alias, sql, params = statement
    return alias, sql, tuple(links if param is LINKS else param for param in params)


def plain(serializer: type[BaseModel]) -> bool:
    """模型的输出是不是就是它的字段原样编码: 没有计算字段, 校验器, 自定义序列化, 别名. 是的话可以直接编码.

    Returns:
        是不是.

    """
    decorators = serializer.__pydantic_decorators__
    return not (
        serializer.__pydantic_computed_fields__
        or decorators.validators
        or decorators.field_validators
        or decorators.root_validators
        or decorators.model_validators
        or decorators.field_serializers
        or decorators.model_serializers
        or any(
            info.alias or info.serialization_alias or info.exclude or info.metadata or info.discriminator
            for info in serializer.model_fields.values()
        )
    )


def own_columns(model: type[Model]) -> set[str]:
    names = set()
    for field in options(model).concrete_fields:
        names |= {field.name, field.attname}
    return names


class Shape:
    """serializer_class 的字段怎么从数据库读出来. 每个视图类在启动时算一次, 声明不对就报错.

    每个字段是模型的列 (按名字或 attname), 或者计算字段 (computed_field, 不读库, 由模型算).
    模型之间不用外键, 资源只输出列和计算字段: 类型是 Pydantic 模型或 list[Model] 而名字不是列的字段, 启动报错.
    """

    def __init__(self, view: type[API]) -> None:
        """按 view 的 model 和 serializer_class 算一次."""
        self.view = view
        model, serializer = view.model, view.serializer_class
        opts = options(model)
        columns = own_columns(model)
        self.names: list[str] = []  # values() 的参数, 也是一行里每个值的位置
        for name, info in serializer.model_fields.items():
            if name not in columns:
                self.refuse(name, info.annotation)
            self.select(name)
        self.column_names = list(serializer.model_fields)  # 在 names 的最前面, 按 serializer_class 的字段顺序
        self.list_names = list(self.names)
        for field in opts.concrete_fields:  # 详情还要建出模型实例, 给对象权限检查用
            self.select(field.attname)
        self.attnames = [(field.attname, self.names.index(field.attname)) for field in opts.concrete_fields]

    def select(self, name: str) -> int:
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    def refuse(self, name: str, annotation: object) -> None:
        view, model = self.view.__name__, self.view.model.__name__
        if names_model(annotation):
            msg = (
                f"{view}.serializer_class 的 {name} 的类型是 Pydantic 模型, 它不是 {model} 的列. "
                "模型之间不用外键, 资源只输出列和计算字段: 别的表的行用 id 列引用 (比如 category_id)."
            )
        else:
            msg = (
                f"{view}.serializer_class 的 {name} 不是 {model} 的列. 字段只能是列, 或者计算字段 "
                "(computed_field). 模型上的 @property 改成 serializer_class 里的计算字段."
            )
        raise ImproperlyConfigured(msg)

    def row(self, values: tuple) -> dict[str, Any]:
        """一行的值 -> serializer_class 的字段, 顺序和声明一样. 后面不在响应里的列不要.

        Returns:
            响应的一行.

        """
        return dict(zip(self.column_names, values, strict=False))

    def rows(self, values: list[tuple]) -> list[dict[str, Any]]:
        return [self.row(item) for item in values]

    def instance(self, values: tuple, alias: str) -> Model:
        """详情的一行建成模型实例, 给对象权限检查用. 这是一条已经在库里的记录.

        Returns:
            模型实例.

        """
        obj = self.view.model(**{attname: values[index] for attname, index in self.attnames})
        obj._state.adding, obj._state.db = False, alias
        return obj

    def row_type(self) -> type | None:
        """直接编码一行用的类型: 字段和 serializer_class 一样的 TypedDict.

        Returns:
            TypedDict, 不能直接编码时是 None.

        """
        serializer = self.view.serializer_class
        if not plain(serializer) or any(names_model(info.annotation) for info in serializer.model_fields.values()):
            return None
        row = TypedDict(
            f"{serializer.__name__}Row", {name: info.annotation for name, info in serializer.model_fields.items()}
        )
        row.__pydantic_config__ = serializer.model_config
        return row


class API:
    """五个资源类的共同部分. 不直接使用."""

    model: ClassVar[type[Model]] = None
    serializer_class: ClassVar[type[BaseModel]] = None
    input_class: ClassVar[type[BaseModel] | None] = None
    actions: ClassVar[tuple[str, ...]] = ()
    lookup_field: ClassVar[str] = "pk"
    filterset_class: ClassVar[type[FilterSet] | None] = None
    filterset_fields: ClassVar[tuple[str, ...]] = ()
    ordering: ClassVar[tuple[str, ...]] = ()
    request_permissions: ClassVar[tuple] = ()  # 进入动作前检查
    object_permissions: ClassVar[tuple] = ()  # 取到对象后检查
    allow_anonymous_write: ClassVar[bool] = False
    status_code: int = 200  # 这个动作成功时的状态码, 由 as_handler 设置

    def __init__(self, request: Request, action: str, params: dict[str, Any]) -> None:
        """一次请求的一个动作. params 是路径参数."""
        self.request = request
        self.action = action
        self.params = params

    # 注册
    @classmethod
    def register(cls, api: BoltAPI, path: str, **options: object) -> None:
        """把这个类的每个动作注册成一条路由. 由 API.viewset 调用."""
        cls.check()
        for action in cls.actions:
            method, detail = ACTIONS[action]
            route = f"{path}/{{{cls.lookup_field}}}" if detail else path
            route_options = dict(options)
            if action in WRITE_ACTIONS and not cls.allow_anonymous_write:
                route_options["guards"] = [IsAuthenticated()]
            if action == "create":
                route_options.setdefault("status_code", 201)
            status_code = cast("int", route_options.get("status_code") or 200)  # 引擎路由的 status_code 是 int
            handler = cls.as_handler(action, route, status_code)
            getattr(api, method)(route, **route_options)(handler)

    @classmethod
    def check(cls) -> None:
        """类声明不符合约定时, 启动就报错.

        Raises:
            ImproperlyConfigured: 声明不符合约定.

        """
        name = cls.__name__
        for attribute in ("model", "serializer_class"):
            if getattr(cls, attribute, None) is None:
                msg = f"{name} 必须声明 {attribute}."
                raise ImproperlyConfigured(msg)
        if not issubclass(cls.serializer_class, BaseModel):
            msg = f"{name}.serializer_class 必须是 Pydantic 模型."
            raise ImproperlyConfigured(msg)
        SHAPES.pop(cls, None)
        cls.shape()  # serializer_class 的每个字段都要能从数据库读出来, 否则这里就报错
        if not set(cls.actions) & set(BODY_ACTIONS):
            return
        input_class = cls.input_class
        if input_class is None or not issubclass(input_class, BaseModel):
            msg = f"{name} 有写入动作, 必须声明 input_class, 并且是 Pydantic 模型."
            raise ImproperlyConfigured(msg)
        opts = options(cls.model)
        fields = set(input_class.model_fields)
        if forbidden := {opts.pk.name, opts.pk.attname, "pk", *OWNER_FIELDS} & fields:
            msg = f"{name}.input_class 不能有主键和所有者字段: {sorted(forbidden)}."
            raise ImproperlyConfigured(msg)
        columns = {field.name for field in opts.concrete_fields} | {field.attname for field in opts.concrete_fields}
        if unknown := fields - columns:
            msg = f"{name}.input_class 的这些字段不是 {cls.model.__name__} 的字段: {sorted(unknown)}."
            raise ImproperlyConfigured(msg)

    @classmethod
    def as_handler(cls, action: str, route: str, status_code: int = 200) -> Callable[..., Awaitable[object]]:
        """动作对应的处理函数. 它的签名决定了引擎怎么取路径参数和请求体, 以及接口文档里写什么.

        Returns:
            处理函数.

        """
        parameters = [Parameter("request", Parameter.POSITIONAL_OR_KEYWORD)]
        parameters += [
            Parameter(name, Parameter.POSITIONAL_OR_KEYWORD, annotation=cls.path_type(name))
            for name in re.findall(r"\{(\w+)\}", route)
        ]
        if action in BODY_ACTIONS:
            body = cls.partial_input() if action == "partial_update" else cls.input_class
            parameters.append(Parameter("data", Parameter.POSITIONAL_OR_KEYWORD, annotation=body))
        returns = cls.page_class() if action == "list" else cls.serializer_class
        signature = Signature(parameters, return_annotation=returns)
        name = cls.get_operation_name(action)

        async def handler(*args: object, **kwargs: object) -> object:
            arguments = signature.bind(*args, **kwargs).arguments
            data = arguments.pop("data", None)
            view = cls(arguments.pop("request"), action, arguments)
            view.status_code = status_code
            try:
                await view.check_request_permissions()
                return await getattr(view, action)(*(() if data is None else (data,)))
            except HTTPException:
                raise
            except Exception:
                report(name)
                raise

        # 引擎和 idempotency 读这些属性, 函数对象上的属性类型检查器不知道
        handler.__signature__ = signature
        handler.__annotations__ = {p.name: p.annotation for p in parameters if p.annotation is not Parameter.empty}
        handler.__annotations__["return"] = returns
        handler.__name__ = handler.__qualname__ = name
        handler.__doc__ = cls.__doc__
        handler.railguns_view = cls
        handler.railguns_action = action
        handler.railguns_idempotent = False
        # 创建支持 Idempotency-Key: 带键时整个处理函数和键在同一个事务里, 和业务接口一样
        return idempotency.idempotent(handler, status_code) if action == "create" else handler

    @classmethod
    def path_type(cls, name: str) -> object:
        """路径参数的类型.

        模型上有 choices 的字段只能是其中的值 (Literal, 接口定义里是 enum),
        整数字段是 int, 其余是 str. 不在 choices 里的值由引擎拒绝 (422), 不会查出一个空列表.

        Returns:
            参数的类型.

        """
        opts = options(cls.model)
        try:
            field = opts.pk if name == "pk" else opts.get_field(name)
        except FieldDoesNotExist:
            return str
        if field.choices:
            return Literal[*(value for value, _ in field.flatchoices)]
        return int if isinstance(field, IntegerField) else str

    @classmethod
    def page_class(cls) -> type[BaseModel]:
        """列表的响应类型. 起一个名字, 接口定义和客户端里就是 ArticleSerializerPage, 而不是 Page_ArticleSerializer_.

        Returns:
            分页的响应模型.

        """
        name = f"{cls.serializer_class.__name__}Page"
        if name not in PAGES:
            page = Page[cls.serializer_class]
            PAGES[name] = type(name, (page,), {"__module__": cls.serializer_class.__module__})
        return PAGES[name]

    @classmethod
    def shape(cls) -> Shape:
        if cls not in SHAPES:
            SHAPES[cls] = Shape(cls)
        return SHAPES[cls]

    @classmethod
    def page_encoder(cls, page_class: type[BaseModel] | None) -> TypeAdapter | None:
        """直接编码的 TypeAdapter: 一页 (page_class), 或者详情的一行 (None).

        每行是字段和 serializer_class 一样的 TypedDict.

        一行就是 serializer_class 声明的列, 从数据库读出来时已经是对的类型, 再按模型校验一遍,
        建一遍实例只是为了编码. 所以 serializer_class 没有计算字段, 校验器, 自定义序列化, 别名,
        字段的类型里也没有 Pydantic 模型时, 直接按同样的字段和类型编码, 输出完全一样. 否则返回 None, 照常校验.

        Returns:
            TypeAdapter, 或者 None.

        """
        if (cls, page_class) in ENCODERS:
            return ENCODERS[cls, page_class]
        row = cls.shape().row_type()
        encoder = None
        if row is not None and page_class is None:
            encoder = TypeAdapter(row)
        elif row is not None and page_class is not None:
            page = TypedDict(
                f"{page_class.__name__}Encoded",
                {
                    name: list[row] if name == "results" else info.annotation
                    for name, info in page_class.model_fields.items()
                },
            )
            page.__pydantic_config__ = cls.serializer_class.model_config
            encoder = TypeAdapter(page)
        ENCODERS[cls, page_class] = encoder
        return encoder

    @classmethod
    def encode_page(cls, page_class: type[BaseModel] | None, page: dict[str, Any]) -> dict[str, Any] | Response:
        """一页 (或详情的一行) 的响应.

        能直接编码时给引擎编好的字节, 引擎原样发出; 否则给字典, 引擎按返回类型校验再编码.

        Returns:
            编好的响应, 或者字典.

        """
        encoder = cls.page_encoder(page_class)
        return page if encoder is None else Response(content=encoder.dump_json(page), media_type="application/json")

    @classmethod
    def partial_input(cls) -> type[BaseModel]:
        """部分更新的请求体: input_class 的每个字段都可以不传. 约束和校验器不变.

        Returns:
            请求体的模型.

        """
        input_class = cast("type[BaseModel]", cls.input_class)  # 有写入动作的类 check() 时已经确认声明了
        fields = {
            name: (info.annotation, FieldInfo.merge_field_infos(info, default=None))
            for name, info in input_class.model_fields.items()
        }
        return create_model(f"{input_class.__name__}Partial", __base__=input_class, **fields)

    @classmethod
    def get_operation_name(cls, action: str) -> str:
        """接口名: 类名去掉 List/Detail/Create 后缀转下划线, 再接动作名. ArticleList + list -> article_list.

        Returns:
            接口名.

        """
        base = re.sub(r"(List|Detail|Create|ViewSet|API)$", "", cls.__name__) or cls.__name__
        return f"{re.sub(r"(?<!^)(?=[A-Z])", "_", base).lower()}_{action}"

    @classmethod
    def get_model(cls) -> type[Model]:
        return cls.model

    # 请求
    @property
    def method(self) -> str:
        return self.request.method

    async def get_user(self) -> AbstractBaseUser | AnonymousUser | None:
        return await self.request.auser() if get_user_id(self.request) else AnonymousUser()

    async def check_request_permissions(self) -> None:
        for permission in self.request_permissions:
            if not await permission.has_permission(self.request, self):
                raise HTTPException(status_code=403, detail="您没有执行该操作的权限。")

    def check_object_permissions(self, obj: Model) -> None:
        for permission in self.object_permissions:
            if not permission.has_object_permission(self.request, self, obj):
                raise HTTPException(status_code=403, detail="您没有执行该操作的权限。")

    # 查询
    async def get_queryset(self) -> QuerySet:
        """读只看启用的记录. 写能取到停用的记录, 这样所有者可以把它重新启用.

        Returns:
            这个动作能看到的记录.

        """
        queryset = self.model._default_manager.all()
        if self.action in WRITE_ACTIONS or not self.has_field("is_active"):
            return queryset
        return queryset.filter(is_active=True)

    async def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """路径里的参数, 再加 django-filter 和排序.

        Returns:
            筛选和排序后的记录.

        Raises:
            HTTPException: 筛选值无效, 400.

        """
        if self.params:
            queryset = queryset.filter(**self.params)
        if self.uses_filters():
            filterset_class = cast("type[FilterSet]", self.get_filterset_class())  # uses_filters() 为真时一定有
            filterset = filterset_class(data=self.request.query, queryset=queryset)
            if not filterset.is_valid():
                raise HTTPException(status_code=400, detail=filterset.errors.get_json_data())
            queryset = filterset.qs
        return queryset.order_by(*self.ordering) if self.ordering else queryset

    def uses_filters(self) -> bool:
        """请求里有没有筛选参数. 没有时不建 filterset: 它每次要走一遍表单校验, 而多数列表请求不带筛选.

        Returns:
            有没有.

        """
        filterset_class = self.get_filterset_class()
        return filterset_class is not None and any(name in self.request.query for name in filterset_class.base_filters)

    @classmethod
    def is_pure(cls) -> bool:
        """读查询是不是只由请求的输入 (路径参数, 查询参数) 决定. 是的话编译好的 SQL 可以复用.

        覆盖了 get_queryset 或 filter_queryset 的类, 查询可能取决于当前用户, 时间或别的任何东西;
        默认管理器覆盖了 get_queryset 的模型也一样. 这些每次都编译.

        Returns:
            是不是.

        """
        if cls not in PURE:
            manager = type(default_manager(cls.model))
            PURE[cls] = (
                cls.get_queryset is API.get_queryset
                and cls.filter_queryset is API.filter_queryset
                and manager.get_queryset is Manager.get_queryset
            )
        return PURE[cls]

    def statement_key(self, *parts: int) -> tuple | None:
        """编译好的读查询的键: 视图类, 动作, 路径参数, 用到的筛选参数, 再加 parts (页码, 每页条数).

        Returns:
            键. None 表示这次不能复用: 查询不只由这些输入决定, 或者某个输入不能做键.

        """
        cls = type(self)
        if not cls.is_pure():
            return None
        filters = ()
        if self.uses_filters():
            if cls.filterset_class is not None:  # 自己写的 filterset 可能取决于时间, 比如 "最近七天"
                return None
            # 整个查询字符串都交给了 filterset, 所以都进键. 日期时间的值按当前时区解释, 时区也进键
            filters = (timezone.get_current_timezone_name(), *sorted(self.request.query.items()))
        key = (cls, self.action, *self.params.items(), filters, *parts)
        try:
            hash(key)
        except TypeError:
            return None
        return key

    async def statement(self, build: Callable[[], Awaitable[Statement]], *parts: int) -> Statement:
        """编译好的读查询. 先查 STATEMENTS, 没有再由 build 编译.

        只有编译成功 (filterset 校验通过) 之后才记下来, 所以命中时可以跳过校验: 无效的筛选值从来不会被记下.

        Returns:
            编译好的查询.

        """
        key = self.statement_key(*parts)
        if key is not None and (found := STATEMENTS.get(key)) is not None:
            return found
        found = await build()
        if key is not None:
            STATEMENTS.put(key, found)
        return found

    @classmethod
    def get_filterset_class(cls) -> type[FilterSet] | None:
        """filterset_class, 或者由 filterset_fields 生成的类. 每个视图类只生成一次.

        Returns:
            filterset 类, 没有筛选时是 None.

        """
        if cls not in FILTERSETS:
            generated = filterset_factory(cls.model, fields=cls.filterset_fields) if cls.filterset_fields else None
            FILTERSETS[cls] = cls.filterset_class or generated
        return FILTERSETS[cls]

    @classmethod
    def has_field(cls, name: str) -> bool:
        fields = cls.model._meta.concrete_fields
        return any(name in {field.name, field.attname} for field in fields)

    @classmethod
    def columns(cls) -> builtins.list[str]:
        """serializer_class 里和模型的列同名的字段, 按 serializer_class 里声明的顺序.

        直接编码的一页 (见 page_encoder) 按行里键的顺序输出, 所以行里的键按 serializer_class 的字段顺序.

        Returns:
            字段名.

        """
        own = own_columns(cls.model)
        return [name for name in cls.serializer_class.model_fields if name in own]

    async def get_object(self) -> Model:
        """取一个对象并检查对象权限. 读走原生连接, 写走 ORM (之后要保存).

        Returns:
            模型实例.

        Raises:
            HTTPException: 没有这个对象, 404.

        """
        if self.action in WRITE_ACTIONS:
            obj = await (await self.get_queryset()).filter(**self.params).afirst()
            if obj is None:
                raise HTTPException(status_code=404, detail="未找到。")
            self.check_object_permissions(obj)
            return obj
        obj, _ = await self.read_object()
        return obj

    async def read_object(self) -> tuple[Model, dict[str, Any]]:
        """详情: 一条语句读出模型的列. 检查对象权限.

        响应和列表里的一行用同一份代码建, 所以完全一样.

        Returns:
            模型实例 (给对象权限检查) 和响应的这一行.

        Raises:
            HTTPException: 没有这个对象, 404.

        """
        shape = self.shape()

        async def build() -> Statement:
            return compile_statement((await self.get_queryset()).filter(**self.params)[:1].values(*shape.names))

        statement = await self.statement(build)
        values = await execute(statement)
        if not values:
            raise HTTPException(status_code=404, detail="未找到。")
        obj = shape.instance(values[0], statement[0])
        self.check_object_permissions(obj)
        return obj, shape.row(values[0])

    # 动作
    async def list(self) -> dict[str, Any] | Response:
        pagination = Pagination(self.request)
        if not pagination.valid:  # 页码不是数字, 或者小于 1. 筛选值无效时仍然先报 400
            await self.filter_queryset(await self.get_queryset())
            raise invalid_page()
        shape = self.shape()

        async def build() -> Statement:
            queryset = await self.filter_queryset(await self.get_queryset())
            return page_statement(queryset, shape.list_names, pagination.size, pagination.number)

        values = await execute(await self.statement(build, pagination.size, pagination.number))
        total = values[0][-1] if values else 0  # 每行最后一列是总数
        return self.encode_page(self.page_class(), pagination.page(total, shape.rows(values)))

    async def retrieve(self) -> dict[str, Any] | Response:
        _, row = await self.read_object()
        return self.encode_page(None, row)

    async def create(self, data: BaseModel) -> Model | dict[str, Any] | Response:
        obj = self.model(**data.model_dump())
        try:
            if (
                not self.native_create()
                or idempotency.HEADER in self.request.headers
                or pre_save.has_listeners(self.model)
                or post_save.has_listeners(self.model)
            ):
                await self.perform_create(obj)
                return obj
            return await self.inserted(obj)
        except IntegrityError as exc:
            if (error := conflict(self.model, exc)) is not None:
                raise error from exc
            raise

    async def perform_create(self, obj: Model) -> None:
        """所有者取自令牌, 不取自请求体."""
        await self.set_owner(obj)
        await obj.asave(force_insert=True)
        if deferred := obj.get_deferred_fields():  # 数据库生成的值读回来, 否则编码响应时会触发同步查询
            await obj.arefresh_from_db(fields=deferred)

    def owner_names(self) -> builtins.list[str]:
        return [name for name in OWNER_FIELDS if self.has_field(name)]

    async def set_owner(self, obj: Model) -> None:
        """所有者字段取自当前用户, 不取自请求体. 模型没有所有者字段时不读用户 (覆盖了 get_user 的类照旧调用它).

        令牌有效, 用户却已删除或停用时是 401: 不用令牌里的 id 写入. 和 request.auser() 的规则一样.

        Raises:
            not_a_user: 令牌里的用户已删除或停用, 401.

        """
        names = self.owner_names()
        if not names and type(self).get_user is API.get_user:
            return
        user = await self.get_user()
        if user is None:  # 令牌里的用户已删除或停用, request.auser() 给 None
            raise not_a_user()
        if user.is_authenticated:
            username = user.username
            values = {"user_id": user.pk, "username": username, "user_avatar": getattr(user, "avatar", "")}
            for name in names:
                setattr(obj, name, values[name])

    @classmethod
    def native_create(cls) -> bool:
        """创建能不能不经过 ORM, 直接在原生连接上执行 INSERT (见 inserted). 不能的时候走 perform_create 和 save().

        类和模型的部分启动后不变, 每个类算一次: 视图没有覆盖 create, perform_create, get_user, inserted;
        模型没有覆盖 save() 一类的方法, 不是多表继承或代理, 没有 order_with_respect_to, 主键只有一列.
        每次再看: 模型有没有 pre_save / post_save 的接收者 (随时可以连上), 请求有没有带 Idempotency-Key
        (带键时整个处理函数在键的事务里, 写入要用 ORM 的连接).

        Returns:
            能不能.

        """
        if cls not in NATIVE_CREATE:
            model = cls.model
            opts = options(model)
            NATIVE_CREATE[cls] = (
                all(
                    getattr(cls, name) is getattr(API, name)
                    for name in ("create", "perform_create", "get_user", "inserted")
                )
                and all(getattr(model, name) is getattr(Model, name) for name in SAVE_METHODS)
                and not opts.parents
                and not opts.proxy
                and opts.order_with_respect_to is None
                and len(opts.pk_fields) == 1
            )
        return NATIVE_CREATE[cls]

    async def inserted(self, obj: Model) -> dict[str, Any] | Response:
        """一条 INSERT ... RETURNING: Django 编译 (字段的 pre_save, 默认值, db_default, 列名都照旧), 原生连接执行.

        所有者字段 (user_id, username, user_avatar) 在同一条语句里从用户表读出: VALUES 换成
        SELECT ... FROM (启用的这个用户) AS owner. 用户已删除或停用时一行也不插入, 是 401. 所以创建总是一次往返.
        RETURNING 响应要的列, 一行就是响应.
        响应的一行和列表, 详情用同一份代码建, 所以 201 的响应体和随后 GET 的完全一样.
        SQL 只取决于视图类和哪些字段用数据库的默认值, 编译一次记在 STATEMENTS 里, 之后每次只准备参数.
        用户表的查询编译不了 (默认管理器改过查询, 在另一个库) 或者 INSERT 不能复用时, 用户由 get_user 读出.

        Returns:
            创建的响应.

        Raises:
            IntegrityError: 违反完整性约束, 和 ORM 抛的一样.
            not_a_user: 令牌里的用户已删除或停用, 401.

        """
        statement = await self.insert_statement(obj, router.db_for_write(self.model, instance=obj))
        try:
            rows = await execute(statement)
        except DriverIntegrityError as exc:  # 和 ORM 一样抛 Django 的 IntegrityError
            raise IntegrityError(*exc.args) from exc
        if not rows:  # 用户已删除或停用, 一行也没有插入
            raise not_a_user()
        [row] = rows
        return self.encode_written(self.shape().row(row))

    async def insert_statement(self, obj: Model, alias: str) -> Statement:
        """这次创建的 INSERT 和参数. 能从用户表读所有者时改写成 INSERT ... SELECT (见 join_owner).

        Returns:
            INSERT 的查询.

        """
        names = self.owner_names()
        user_id = get_user_id(self.request) if names else None
        owner = self.owner_statement(names, alias) if user_id is not None else None
        opts = self.model._meta
        if owner is not None and any(opts.get_field(name).has_db_default() for name in names):
            owner = None
        if user_id is not None and owner is None:
            await self.set_owner(obj)
        fields, values, defaults, pk_set = self.insert_values(obj)
        key = (type(self), "create", alias, pk_set, defaults, owner is not None)
        if (found := STATEMENTS.get(key)) is not None:
            statement = (alias, found[1], self.insert_params(alias, fields, values, defaults, names if owner else ()))
        elif self.reusable_insert(fields, values, defaults, compiled := self.compile_insert(obj, alias, fields)):
            if owner is not None:
                compiled = self.join_owner(compiled, fields, defaults, names, owner)
            STATEMENTS.put(key, compiled)
            params = self.insert_params(alias, fields, values, defaults, names if owner else ())
            statement = (alias, compiled[1], params)
        elif owner is not None:  # 不能改写成 SELECT: 用户由 get_user 读出, 再照常编译
            await self.set_owner(obj)
            for field in fields:
                if field.attname in names:
                    setattr(obj, field.attname, field.pre_save(obj, add=True))
            return self.compile_insert(obj, alias, fields)
        else:
            return compiled
        if owner is None or user_id is None:  # owner 只在有 user_id 时才有
            return statement
        return alias, statement[1], (*statement[2], *bind(owner, [owner_pk(user_id)])[2])

    def insert_values(self, obj: Model) -> tuple[builtins.list[Field], builtins.list, tuple, bool]:
        """插入的字段和值, 和 save() 一样: 主键的默认值, 每个字段 pre_save 一次 (auto_now 在这里取时间).

        值写回对象, 编译时按 raw 取, 不再调用 pre_save.

        Returns:
            字段, 值, 每个值是不是数据库默认值, 主键有没有值.

        """
        opts = self.model._meta
        pk = opts.pk
        pk_unset = not obj._is_pk_set(opts)
        if pk_unset and not isinstance(getattr(obj, pk.attname), DatabaseDefault):
            setattr(obj, pk.attname, pk.get_pk_value_on_save(obj))
        pk_set = obj._is_pk_set(opts)
        fields = [
            field
            for field in opts.local_concrete_fields
            if not field.generated and (pk_set or field is not opts.auto_field)
        ]
        values = []
        for field in fields:
            value = field.pre_save(obj, add=True)
            setattr(obj, field.attname, value)
            values.append(value)
        return fields, values, tuple(isinstance(value, DatabaseDefault) for value in values), pk_set

    @staticmethod
    def owner_statement(names: builtins.list[str], alias: str) -> Statement | None:
        """令牌里的这个用户 (启用的) 的所有者字段.

        SELECT pk AS railguns_user_id, username AS railguns_username, ...
        用户 id 是一个数组参数 (见 AnyOf), 每个用户模型和字段组合只编译一次.

        和 request.auser() 一样: 用户要存在, 有 is_active 字段时要启用. 默认管理器改过查询,
        用户表在另一个库, 或者 avatar 不是列时返回 None, 用户由 get_user 读出.

        Returns:
            用户表的查询, 或者 None.

        """
        user_model = get_user_model()
        key = (user_model, "owner", alias, tuple(names))
        if (found := STATEMENTS.get(key)) is not None:
            return found
        columns = own_columns(user_model)
        manager = default_manager(user_model)
        if (
            type(manager).get_queryset is not Manager.get_queryset
            or ("username" in names and "username" not in columns)
            or ("user_avatar" in names and hasattr(user_model, "avatar") and "avatar" not in columns)
            or (router.db_for_read(user_model) or "default") != alias
        ):
            return None
        sources = {
            "user_id": F("pk"),
            "username": F("username"),
            "user_avatar": F("avatar") if "avatar" in columns else Value(""),
        }
        queryset = manager.filter(AnyOf(F("pk"), LINKS))
        if "is_active" in columns:
            queryset = queryset.filter(is_active=True)
        statement = compile_statement(queryset.values(**{f"railguns_{name}": sources[name] for name in names}))
        STATEMENTS.put(key, statement)
        return statement

    @staticmethod
    def join_owner(
        statement: Statement, fields: builtins.list[Field], defaults: tuple, names: builtins.list[str], owner: Statement
    ) -> Statement:
        """INSERT ... VALUES (%s, ...) 改写成 INSERT ... SELECT %s, ..., owner.railguns_username, ... FROM (owner).

        只在每个值都是一个 %s 时调用 (见 reusable_insert), 所以 VALUES 的样子是确定的. 参数由 insert_params 准备.

        Returns:
            改写后的 INSERT, 参数为空.

        Raises:
            ImproperlyConfigured: 没有认出 VALUES.

        """
        alias, sql, _ = statement
        kept = [field for field, default in zip(fields, defaults, strict=True) if not default]
        placeholders = f"VALUES ({", ".join(["%s"] * len(kept))})"
        if sql.count(placeholders) != 1:
            msg = f"没有认出 INSERT 的 VALUES: {sql}"
            raise ImproperlyConfigured(msg)
        selected = ", ".join(
            f'"railguns_owner"."railguns_{field.attname}"' if field.attname in names else "%s" for field in kept
        )
        # 两段都是 Django 编译的 SQL, 值都在参数里
        joined = f'SELECT {selected} FROM ({owner[1]}) AS "railguns_owner"'
        return alias, sql.replace(placeholders, joined), ()

    @staticmethod
    def insert_params(
        alias: str,
        fields: builtins.list[Field],
        values: builtins.list,
        defaults: tuple,
        names: builtins.list[str] | tuple,
    ) -> tuple:
        """INSERT 的参数: 不用数据库默认值, 也不从用户表读的字段, 按字段自己准备.

        Returns:
            参数.

        """
        database = connections[alias]
        return tuple(
            field.get_db_prep_save(value, connection=database)
            for field, value, default in zip(fields, values, defaults, strict=True)
            if not default and field.attname not in names
        )

    def compile_insert(self, obj: Model, alias: str, fields: builtins.list[Field]) -> Statement:
        """INSERT 由 Django 编译. 字段的值已经 pre_save 过 (见 inserted), 所以按 raw 编译.

        Returns:
            INSERT 的查询.

        """
        shape, opts = self.shape(), self.model._meta
        query = InsertQuery(self.model)
        query.insert_values(fields, [obj], raw=True)
        compiler = query.get_compiler(using=alias)
        compiler.returning_fields = [opts.get_field(name) for name in shape.column_names]
        [(sql, params)] = compiler.as_sql()
        return alias, sql, tuple(params)

    @staticmethod
    def reusable_insert(
        fields: builtins.list[Field], values: builtins.list, defaults: tuple, statement: Statement
    ) -> bool:
        """编译出的 INSERT 能不能记下来, 之后只换参数.

        每个值都是一个普通的 %s 参数, 不是表达式, 也没有自定义占位符.
        再核对一遍: 按字段自己准备出的参数和 Django 编译出的完全一样.

        Returns:
            能不能.

        """
        if sum(defaults) == len(fields) or any(
            getattr(field, "get_placeholder_sql", None) is not None
            or getattr(field, "get_placeholder", None) is not None
            or (hasattr(value, "resolve_expression") and not default)
            for field, value, default in zip(fields, values, defaults, strict=True)
        ):
            return False
        alias, _, params = statement
        database = connections[alias]
        prepared = tuple(
            field.get_db_prep_save(value, connection=database)
            for field, value, default in zip(fields, values, defaults, strict=True)
            if not default
        )
        try:
            return prepared == params and not any(hasattr(param, "as_sql") for param in params)
        except TypeError, ValueError:
            return False

    def encode_written(self, row: dict[str, Any]) -> dict[str, Any] | Response:
        """创建的响应: 和详情一样能直接编码时给编好的字节, 带上这个动作的状态码.

        Returns:
            编好的响应, 或者字典.

        """
        encoder = self.page_encoder(None)
        if encoder is None:
            return row
        return Response(content=encoder.dump_json(row), status_code=self.status_code, media_type="application/json")

    async def update(self, data: BaseModel) -> Model:
        return await self.write(data.model_dump())

    async def partial_update(self, data: BaseModel) -> Model:
        return await self.write(data.model_dump(exclude_unset=True))

    async def write(self, values: dict[str, Any]) -> Model:
        obj = await self.get_object()
        for name, value in values.items():
            setattr(obj, name, value)
        try:
            await self.perform_update(obj)
        except IntegrityError as exc:
            if (error := conflict(self.model, exc)) is not None:
                raise error from exc
            raise
        return obj

    async def perform_update(self, obj: Model) -> None:
        await obj.asave()


class CreateAPI(API):
    """创建 API."""

    actions = ("create",)


class ListAPI(API):
    """列表 API."""

    actions = ("list",)


class ListCreateAPI(API):
    """列表 & 创建 API."""

    actions = ("list", "create")


class RetrieveAPI(API):
    """详情 API."""

    actions = ("retrieve",)


class RetrieveUpdateAPI(API):
    """详情 & 更新 API."""

    actions = ("retrieve", "update", "partial_update")
