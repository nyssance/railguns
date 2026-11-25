"""资源接口: 增, 查, 改.

五个类, 每个类对应固定的几条路由, 没有别的写法: CreateAPI, ListAPI, ListCreateAPI, RetrieveAPI, RetrieveUpdateAPI.

    @api.viewset("/articles", auth=AUTH, guards=[AllowAny()], tags=["articles"])
    class ArticleList(ListCreateAPI):
        model = Article
        serializer_class = ArticleSerializer   # 响应, Pydantic 模型
        input_class = ArticleInput             # 请求体, Pydantic 模型. 有写入动作的类必须声明
        filterset_fields = ("score",)

约定:

- 处理函数是同步的, 数据访问就是 Django 的 ORM: 默认值, 信号, save(), auto_now, db_default 都照常生效.
  引擎默认在它的线程池里执行同步的处理函数, 一个请求一次线程切换, 查询和响应都在这个线程里.
- 响应里只有 serializer_class 声明的字段, 每个都是列或计算字段. 模型之间不用外键, 没有关联.
  请求体里只有 input_class 声明的字段能写进模型,
  主键和所有者字段不允许出现在 input_class 里, 所以请求体改不了它们.
- 写入默认要求登录, 在 Rust 里拦截, 未登录的请求不进 Python.
- 创建支持 Idempotency-Key: 带同一个键重试, 只创建一次 (见 idempotency).
"""

import re
from inspect import Parameter, Signature
from typing import Any, ClassVar, Literal, cast, get_args
lazy from collections.abc import Callable

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db import IntegrityError, connections, router
from django.db.models import IntegerField, Model, QuerySet, UniqueConstraint
from django_filters.filterset import FilterSet, filterset_factory
from freeman.auth import IsAuthenticated
from freeman.exceptions import HTTPException
from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
lazy from django.contrib.auth.base_user import AbstractBaseUser
lazy from freeman import BoltAPI
lazy from freeman.request import Request

from railguns.django.db._introspect import options

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
UNIQUE: dict[tuple[type, str], dict[str, list[str]]] = {}  # (模型, 数据库别名) -> 唯一约束名 -> 字段名


def names_model(annotation: object) -> bool:
    """类型里有没有 Pydantic 模型.

    Returns:
        有没有.

    """
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return True
    return any(names_model(arg) for arg in get_args(annotation))


def not_a_user() -> HTTPException:
    """令牌有效, 但用户已删除或停用.

    Returns:
        401 的异常.

    """
    return HTTPException(status_code=401, detail={"code": "not_authenticated", "detail": "用户不存在或已停用。"})


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


def own_columns(model: type[Model]) -> set[str]:
    names = set()
    for field in options(model).concrete_fields:
        names |= {field.name, field.attname}
    return names


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
        cls.check_fields()
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
        if unknown := fields - own_columns(cls.model):
            msg = f"{name}.input_class 的这些字段不是 {cls.model.__name__} 的字段: {sorted(unknown)}."
            raise ImproperlyConfigured(msg)

    @classmethod
    def check_fields(cls) -> None:
        """serializer_class 的每个字段都是模型的列 (按名字或 attname). 计算字段 (computed_field) 不读库, 不在其中.

        模型之间不用外键, 资源只输出列和计算字段.

        Raises:
            ImproperlyConfigured: 有字段不是列.

        """
        view, model = cls.__name__, cls.model.__name__
        columns = own_columns(cls.model)
        for name, info in cls.serializer_class.model_fields.items():
            if name in columns:
                continue
            if names_model(info.annotation):
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

    @classmethod
    def as_handler(cls, action: str, route: str, status_code: int = 200) -> Callable[..., object]:
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

        def handler(*args: object, **kwargs: object) -> object:
            arguments = signature.bind(*args, **kwargs).arguments
            data = arguments.pop("data", None)
            view = cls(arguments.pop("request"), action, arguments)
            try:
                view.check_request_permissions()
                return getattr(view, action)(*(() if data is None else (data,)))
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
        return name in own_columns(cls.model)

    # 请求
    @property
    def method(self) -> str:
        return self.request.method

    def get_user(self) -> AbstractBaseUser | AnonymousUser | None:
        return self.request.user if get_user_id(self.request) else AnonymousUser()

    def check_request_permissions(self) -> None:
        for permission in self.request_permissions:
            if not permission.has_permission(self.request, self):
                raise HTTPException(status_code=403, detail="您没有执行该操作的权限。")

    def check_object_permissions(self, obj: Model) -> None:
        for permission in self.object_permissions:
            if not permission.has_object_permission(self.request, self, obj):
                raise HTTPException(status_code=403, detail="您没有执行该操作的权限。")

    # 查询
    def get_queryset(self) -> QuerySet:
        """读只看启用的记录. 写能取到停用的记录, 这样所有者可以把它重新启用.

        Returns:
            这个动作能看到的记录.

        """
        queryset = self.model._default_manager.all()
        if self.action in WRITE_ACTIONS or not self.has_field("is_active"):
            return queryset
        return queryset.filter(is_active=True)

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """路径里的参数, 再加 django-filter 和排序.

        Returns:
            筛选和排序后的记录.

        Raises:
            HTTPException: 筛选值无效, 400.

        """
        if self.params:
            queryset = queryset.filter(**self.params)
        filterset_class = self.get_filterset_class()
        # 请求里没有筛选参数时不建 filterset: 它每次要走一遍表单校验, 而多数列表请求不带筛选
        if filterset_class is not None and any(name in self.request.query for name in filterset_class.base_filters):
            filterset = filterset_class(data=self.request.query, queryset=queryset)
            if not filterset.is_valid():
                raise HTTPException(status_code=400, detail=filterset.errors.get_json_data())
            queryset = filterset.qs
        return queryset.order_by(*self.ordering) if self.ordering else queryset

    def get_object(self) -> Model:
        """取一个对象并检查对象权限.

        Returns:
            模型实例.

        Raises:
            HTTPException: 没有这个对象, 404.

        """
        obj = self.get_queryset().filter(**self.params).first()
        if obj is None:
            raise HTTPException(status_code=404, detail="未找到。")
        self.check_object_permissions(obj)
        return obj

    # 动作
    def list(self) -> dict[str, Any]:
        """一页: 这一页的行一条查询, 只读 serializer_class 的列; 总数一条查询.

        Returns:
            分页的响应.

        Raises:
            invalid_page: 页码无效, 或者超出最后一页, 404.

        """
        queryset = self.filter_queryset(self.get_queryset())  # 筛选值无效时先报 400
        page = Pagination(self.request)
        if not page.valid:
            raise invalid_page()
        rows = queryset[page.offset : page.offset + page.size].values(*self.serializer_class.model_fields)
        return page.page(queryset.count(), list(rows))

    def retrieve(self) -> Model:
        return self.get_object()

    def create(self, data: BaseModel) -> Model:
        obj = self.model(**data.model_dump())
        try:
            self.perform_create(obj)
        except IntegrityError as exc:
            if (error := conflict(self.model, exc)) is not None:
                raise error from exc
            raise
        return obj

    def perform_create(self, obj: Model) -> None:
        """所有者取自令牌, 不取自请求体."""
        self.set_owner(obj)
        obj.save(force_insert=True)

    def set_owner(self, obj: Model) -> None:
        """所有者字段取自当前用户, 不取自请求体. 模型没有所有者字段时不读用户 (覆盖了 get_user 的类照旧调用它).

        令牌有效, 用户却已删除或停用时是 401: 不用令牌里的 id 写入.

        Raises:
            not_a_user: 令牌里的用户已删除或停用, 401.

        """
        names = [name for name in OWNER_FIELDS if self.has_field(name)]
        if not names and type(self).get_user is API.get_user:
            return
        user = self.get_user()
        if user is None:  # 令牌里的用户已删除或停用, request.user 是 None
            raise not_a_user()
        if user.is_authenticated:
            values = {"user_id": user.pk, "username": user.username, "user_avatar": getattr(user, "avatar", "")}
            for name in names:
                setattr(obj, name, values[name])

    def update(self, data: BaseModel) -> Model:
        return self.write(data.model_dump())

    def partial_update(self, data: BaseModel) -> Model:
        return self.write(data.model_dump(exclude_unset=True))

    def write(self, values: dict[str, Any]) -> Model:
        obj = self.get_object()
        for name, value in values.items():
            setattr(obj, name, value)
        try:
            self.perform_update(obj)
        except IntegrityError as exc:
            if (error := conflict(self.model, exc)) is not None:
                raise error from exc
            raise
        return obj

    def perform_update(self, obj: Model) -> None:
        obj.save()


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
