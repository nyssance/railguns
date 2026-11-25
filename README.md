# RailgunS

[![Downloads](https://pepy.tech/badge/railguns)](https://pepy.tech/project/railguns)
[![PyPI](https://img.shields.io/pypi/v/railguns)](https://pypi.org/project/RailgunS/)
[![Python](https://img.shields.io/pypi/pyversions/railguns)](https://www.python.org)
[![Django](https://img.shields.io/pypi/djversions/railguns)](https://www.djangoproject.com)
[![License](https://img.shields.io/pypi/l/railguns)](https://opensource.org/licenses/MIT)

Only My Railgun

---

## Vendor

框架用到的库

- [Django](https://www.djangoproject.com)
- [Freeman](https://github.com/nyssance/freeman)
- [PostgreSQL](https://www.postgresql.org/)（[psycopg](https://www.psycopg.org/psycopg3/docs/)）

部署

- [Gunicorn](https://www.gunicorn.org)
- [uvicorn](https://www.uvicorn.org)

常用库

- [Django CKEditor 5](https://github.com/hvlads/django-ckeditor-5)
- [Django Filter](https://django-filter.readthedocs.io)
- [django-htmlmin](https://github.com/cobrateam/django-htmlmin)
- [redis-py](https://github.com/redis/redis-py)

## 核心思想

让后端代码没有发挥空间: 同一个需求, 谁来写, 用什么工具写, 产出都一样.

- **模型**从固定的基类里选, 字段名, 类型, 长度随之确定
- **模型不用外键**: 没有 `ForeignKey` / `OneToOneField` / `ManyToManyField`, 别的表的行用 id 列引用 (`user_id`),
  声明了系统检查报错 (`railguns.E003`). 资源接口只输出列和计算字段. 确实要用外键的应用列在 `RAILGUNS_FOREIGN_KEY_APPS` 里,
  整个应用不检查
- **接口**只有两种: 资源接口 (增查改) 和业务接口 (其余所有), 各有一种固定写法
- **权限**从一组有限的类里选, 不现写
- **命名**由库决定, 文档里的接口名和生成的客户端方法名都是确定的
- **验证**是约定的一部分: 权限矩阵, 字段契约, 新旧比对

每个项目都一样的东西 (登录, 上传签名, 后台, 国际化) 只在库里出现一次, 项目只挂载.

## 安装

```shell
uv add railguns
```

| | 支持范围 |
|---|---|
| Python | 3.15 |
| Django | 6.1 |
| Freeman | 0.1 |
| 数据库 | 只支持 PostgreSQL, 并且必须配连接池. 不符合时启动报错 |

`INSTALLED_APPS` 里要有 `"freeman"` 和 `"railguns"`.

```python
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    ...,
    "OPTIONS": {"pool": {"min_size": 2, "max_size": 16}}
}}
TEST_RUNNER = "railguns.testing.runner.Runner"
```

## 快速开始

```python
# 项目的 api.py, 用 python manage.py runbolt 启动
from railguns.rest_framework.api import API
from railguns.urls import api as railguns_api

from .apps.articles.api import api as articles_api

api = API()
api.mount("", articles_api)
api.mount("/api/v1", railguns_api)  # 登录, 刷新, 上传签名, 下载签名
api.mount_django("/", clear_root_path=True)  # 后台等 Django 页面, 放最后
```

项目里只用 `API`, 不直接用引擎的 `BoltAPI`.

## 模型

```
DateTimeModelMixin   created_time, updated_time
  └ BaseModel        + is_active, 默认按主键倒序
      └ OwnerModel   + user_id, username, user_avatar
          └ PostModel + title, summary, images, tags
```

```python
from railguns.django.db.models import PostModel


class Article(PostModel):
    score = models.IntegerField(default=0)
```

## 资源接口

五个类: `CreateAPI`, `ListAPI`, `ListCreateAPI`, `RetrieveAPI`, `RetrieveUpdateAPI`, 没有别的.
读的类填 `model` 和 `serializer_class`, 有创建或更新的类再填 `input_class`. 两个都是 Pydantic 模型.

| 类 | 读取 | 写入 |
|---|---|---|
| `ListAPI` | 列表, 只含 `is_active=True` | |
| `RetrieveAPI` | 详情, 只含 `is_active=True` | |
| `CreateAPI` | | 创建 |
| `ListCreateAPI` | 列表 | 创建 |
| `RetrieveUpdateAPI` | 详情 | 更新 (PUT, PATCH) |

```python
from freeman.auth import AllowAny
from pydantic import BaseModel
from railguns.rest_framework.auth import access_auth
from railguns.rest_framework.generics import ListCreateAPI, RetrieveUpdateAPI
from railguns.rest_framework.permissions import IsOwnerOrReadOnly


class ArticleSerializer(BaseModel):  # 响应: 客户端能拿到的字段
    id: int
    title: str
    score: int
    user_id: int


class ArticleInput(BaseModel):  # 请求体: 客户端能写的字段
    title: str
    score: int = 0


@api.viewset("/api/v1/articles", auth=[access_auth], guards=[AllowAny()], tags=["articles"])
class ArticleList(ListCreateAPI):
    model = Article
    serializer_class = ArticleSerializer
    input_class = ArticleInput
    filterset_fields = ("score",)


@api.viewset("/api/v1/articles", auth=[access_auth], guards=[AllowAny()], tags=["articles"])
class ArticleDetail(RetrieveUpdateAPI):
    model = Article
    serializer_class = ArticleSerializer
    input_class = ArticleInput
    object_permissions = (IsOwnerOrReadOnly(),)
```

基类保证的行为:

- 响应里只有 `serializer_class` 声明的字段. 每个字段必须是模型的列, 或者计算字段 (`computed_field`).
  别的字段 (包括模型上的 `@property`, 类型是 Pydantic 模型或 `list[Model]` 的嵌套字段) 启动就报错:
  列表只从数据库读列, 读不到它们. 列表, 详情, 写入的响应
  用同一份代码建, 同一条记录输出完全一样
- 请求体里只有 `input_class` 声明的字段能写进模型. 主键和所有者字段不允许出现在 `input_class` 里, 声明了启动就报错
- 写入必须登录 (`allow_anonymous_write = True` 可放开), 在 Rust 里拦截, 所以先判断登录再校验参数
- 创建时 `user_id` / `username` / `user_avatar` 取自当前用户, 和 INSERT 在同一条语句里从用户表读出.
  用户已删除或停用时是 401, 不写入. 创建成功返回 201. 违反唯一约束 (创建, 更新) 是 409, `fields` 里是约束的字段
- PATCH 只改请求体里出现的字段, PUT 把没出现的字段改回默认值
- 读 (列表, 详情) 不经过 ORM 的线程池: 查询由 Django 编译成 SQL, 交给原生异步连接执行.
  创建的 INSERT 也由 Django 编译 (默认值, `db_default`, `auto_now` 照旧), `RETURNING` 响应要的列, 原生连接上一次往返.
  模型有 `pre_save` / `post_save` 的接收者, 覆盖了 `save()`, 视图覆盖了 `perform_create` / `get_user`, 或者带了
  `Idempotency-Key` 时, 创建照旧走 ORM. 更新用 ORM, 模型上的默认值, 信号, `save()` 照常生效
- 创建支持 `Idempotency-Key`, 不用声明, 见下面的 [幂等](#幂等)

### 读得快的原因

- 一页只发一条语句: 总数作为标量子查询放在这一页的每一行后面, 一次往返. 不用 `count(*) OVER ()`, 它慢三倍
- 编译好的 SQL 按请求的输入记下来 (每个进程最多 4096 条, 最久没用的先丢), 同样的请求不再编译.
  编译比执行还贵, 列表的吞吐因此是原来的 2.4 倍, 详情是 3 倍. 键是视图类, 动作, 路径参数, 用到的筛选参数, 页码,
  每页条数, 所以不同的用户, 不同的路径参数不会拿到别人的查询. 记下的只是 SQL, 每次都查最新的数据.
  覆盖了 `get_queryset` 或 `filter_queryset` 的类 (查询可能取决于当前用户或时间), 用了自己写的 `filterset_class`
  的筛选请求, 默认管理器覆盖了 `get_queryset` 的模型, 每次都编译. 无效的筛选值不会被记下, 每次都是 400
- `serializer_class` 没有计算字段, 校验器, 自定义序列化, 别名时, 一页 (和详情) 直接按字段编码, 不再逐行校验,
  输出完全一样. 有计算字段时照常校验, 因为计算字段要从实例上算

可选的类属性: `filterset_fields` / `filterset_class` (django-filter), `ordering`, `object_permissions`,
`request_permissions`, `lookup_field`.

路径参数的类型从模型字段推导: 有 `choices` 的字段只能是其中的值 (接口定义里是 enum), 其余值由引擎拒绝 (422),
不会查出一个空列表; 整数字段是 `int`; 其余是 `str`. `/exams/{category}` 这样的路径不用自己校验.

### 分页

列表返回 `{"count", "next", "previous", "results"}`. 查询参数 `page` 和 `page_size`,
每页默认 20 条, 上限 1000. 页码无效返回 404.

业务接口自己分页时用同一份代码 (`pagination.Pagination`), 参数, 上限, 404 和链接都一样. 处理函数不声明这两个参数,
返回类型是 `Page[T]` 的子类时, 接口定义里自动带上:

```python
from railguns.rest_framework.pagination import Page, Pagination


class TitlePage(Page[Title]):
    """标题的一页."""


async def titles(request) -> TitlePage:
    pagination = Pagination.of(request)  # 页码无效时 404
    count, rows = await run(services.titles, actor(request), pagination.offset, pagination.size)
    return pagination.page(count, rows)  # 超出最后一页时 404
```

### 响应里的图片和标签

`mixins` 里的字段 Mixin 只提供方法, 在模型的派生字段里调用:

```python
@computed_field
@property
def image_list(self) -> dict | str:
    return ImagesFieldMixin().get_images(self)
```

### 错误

所有错误只有一种格式, 不能改:

```json
{"code": "validation", "detail": "...", "fields": [{"loc": ["body", "title"], "msg": "...", "type": "missing"}]}
```

`code` 给程序判断, `detail` 给人看, `fields` 只在有字段错误时出现, 并且一次给全. `loc` 的每一段都是字符串.
未登录, 没有权限, 路径不存在, 参数类型不对, 请求体校验失败, 业务错误, 未处理的异常, 都是这一种.

## 业务接口

增查改 (五个资源类) 以外的接口都是业务接口, 固定两层.

```python
# api.py: 只做三件事, 认证 / 收参数 / 回结果
from railguns.rest_framework.actions import actor, run


async def publish(request, pk: int, data: Publish):
    return await run(services.publish, actor(request), pk, data)


api.post("/articles/{pk}/publish", auth=[access_auth], guards=[IsAuthenticated()])(publish)
```

```python
# services.py: 纯业务. 不碰 request, 不拼响应, 出错抛业务异常
from railguns.rest_framework.errors import NotFound, PermissionDenied


def publish(actor, pk, data):
    article = Article.objects.filter(pk=pk).first()
    if article is None:
        raise NotFound("没有这篇文章")
    if article.user_id != actor.user_id and not actor.user.is_staff:
        raise PermissionDenied("不是你的文章")
    ...
```

`run` 做的事:

- 同步函数在线程里执行, 默认整个包在一个事务里, 出错全部回滚 (`atomic=False` 关闭). 异步函数直接执行
- 业务异常转成 `{"code": "permission_denied", "detail": "不是你的文章"}`. `code` 给程序判断, `detail` 给人看
- Django 的 `ValidationError` (`full_clean()` 抛出的) 不用转换, 就是 400, 每个字段的错误在 `fields` 里:
  `{"code": "invalid", "detail": "...", "fields": [{"loc": ["email"], "msg": "...", "type": "invalid"}]}`.
  要自己的 code 时 `raise BusinessError.from_validation(exc, code="invalid_account")`
- 其他异常记到 `django.request` 日志再抛出. 管理员告警邮件走的就是这个日志

| 异常 | 状态码 | 默认 code |
|---|---|---|
| `BusinessError` | 400 | `invalid` |
| `PermissionDenied` | 403 | `permission_denied` |
| `NotFound` | 404 | `not_found` |
| `Conflict` | 409 | `conflict` |
| `TooManyRequests` | 429 | `rate_limited` |
| `BadGateway` | 502 | `bad_gateway`: 上游 (短信, 支付) 返回了失败 |
| `ServiceUnavailable` | 503 | `service_unavailable`: 上游暂时不可用, 可以稍后重试 |

每个异常都可以 `code="..."` 换成自己的 code, 用 `fields=[...]` 带上字段错误. 默认 code 和引擎自己的错误一样
(引擎限流也是 `rate_limited`).

### 幂等

按 IETF 的 [Idempotency-Key 草案](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/):
客户端在 POST 上带 `Idempotency-Key: "<唯一值>"` (不带引号也可以), 网络超时或重复点击时用同一个键重试, 数据只写一次.

| 情况 | 响应 |
|---|---|
| 第一次 | 照常处理, 存下响应 (状态码和响应体) 和请求的指纹 (方法, 路径, 请求体) |
| 同一个键, 同样的请求 | 存下的响应, 不再处理 |
| 同一个键, 不同的请求 | 422 `idempotency_key_reused` |
| 同一个键的第一次请求还在处理 | 409 `idempotency_key_in_use` |
| 键不是 1 到 255 个可见的 ASCII 字符 | 400 `invalid_idempotency_key` |
| 未登录 | 401: 键按用户隔离, 不同的用户可以用同一个键 |

资源接口的创建动作自动支持. 业务接口在注册时打开, 处理函数照常写:

```python
async def verify(request, data: VerificationInput) -> Session:
    return await session(await run(services.verify, actor(request), data))  # run 之后接着签发令牌


api.post("/users/verify", idempotent=True, auth=[access_auth], guards=[IsAuthenticated()])(verify)
```

- 带键的请求, 整个处理函数在一个数据库事务里执行, 存下的是它最后返回的响应. 所以 `run` 之后还可以接着处理,
  重试拿到的是同一份响应 (比如同一对令牌), 业务函数不再执行. 里面的 `run` 是这个事务里的保存点

- 只存成功的响应, 并且和这次请求写入的数据在同一个事务里提交. 请求失败 (业务错误, 异常, 包括 `run` 之后的处理出错)
  时全部回滚, 什么都不留下, 可以重试. 数据库以外的副作用 (缓存, 短信) 不随事务回滚, 和不带键时一样
- 不会重复执行靠的是 `(user_id, key)` 上的唯一约束, 不靠先查再插. 进行中的请求由事务级的咨询锁表示,
  进程崩溃时锁随事务释放, 不会留下一直"处理中"的键
- 键保留 24 小时, 过期的当作没用过. 定时运行 `python manage.py clearidempotencykeys` 删掉过期的行.
  表由 railguns 的迁移创建, 部署时 `migrate`
- 接口定义里, 这些接口有可选的请求头参数 `Idempotency-Key`. 不带这个头的请求和以前完全一样

`actor(request)` 只从令牌里取 `user_id`, 不查库. 需要用户的其他信息时用 `actor.user` (异步函数里用
`await actor.auser()`), 每次请求只查一次. 不从令牌读"是否员工"这类信息, 因为签发之后用户的状态可能已经变了.

这样写的业务函数可以脱离接口单独测试, 定时任务和管理命令也能直接调用.

## 认证

`railguns.urls.api` 提供:

| 接口 | 请求 | 返回 |
|---|---|---|
| `POST /auth/login` | `username`, `password` | `token`, `access`, `refresh`, 加上项目指定的用户资料 |
| `POST /auth/refresh` | `refresh` | 新的 `access` 和 `refresh` |

- 访问令牌 5 分钟, 刷新令牌 1 天
- 刷新令牌只能用一次. 用过的再用, 这一串令牌全部作废
- 接口上写 `auth=[access_auth]` 接受访问令牌. 需要同时接受后台登录会话的接口加上 `SessionAuthentication()`

登录时附带返回的用户资料由项目指定:

```python
RAILGUNS_LOGIN_PROFILE = "myproject.apps.accounts.services.profile"  # def profile(user) -> Profile
```

函数必须声明返回类型, 并且是 Pydantic 模型, 否则启动报错. 登录的响应类型 `LoginResult` 由它生成: 资料的字段和
`token`, `access`, `refresh` 在同一层, 接口定义里每个字段都有类型. 不配置时只有令牌. 注册这类之后直接是登录状态的接口,
用 `auth.session(user)` 得到同样的内容.

`POST /auth/logout` 登出这一次登录: 带访问令牌, 请求体里给刷新令牌, 两个一起作废, 其他设备不受影响.
`POST /auth/logout-all` 登出所有设备: 所有刷新令牌立刻作废. 其他设备手上的访问令牌活到自己过期, 最长 5 分钟.

## 权限

| 类 | 写在 | 规则 |
|---|---|---|
| `IsMe` | `object_permissions` | 对象就是当前用户 |
| `IsMeOrReadOnly` | `object_permissions` | 同上, 读取不限 |
| `IsOwner` | `object_permissions` | 对象的 `user_id` 是当前用户 |
| `IsOwnerOrReadOnly` | `object_permissions` | 同上, 读取不限 |
| `IsRelationOrReadOnly` | `object_permissions` | 当前用户是 `from_id` 或 `to_id`, 读取不限 |
| `IsOwnerOnList` | `request_permissions` | 路径里的查找字段是当前用户 |
| `BlacklistPermission(model)` | `request_permissions` | 来源地址不在黑名单表里 |

引擎的 `guards` 在 Rust 里按令牌判断, 拿不到数据库对象. 所以"是否登录"用 `guards`, 涉及具体对象的用上面这些类.

## 文件存储

| 接口 | 作用 |
|---|---|
| `POST /upload-params/{cloud}` | 取直传到对象存储的签名参数. `cloud` 为 `aliyun` 或 `aws` |
| `GET /download-url/{cloud}?url=` | 给私有文件的地址签名, 10 分钟有效 |

访问令牌和后台登录会话都可以调用. 传到 media 以外的桶需要员工身份. 只给自己的桶签名.

## 接口文档

```python
from freeman.openapi import OpenAPIConfig
from railguns.rest_framework.schemas.openapi import AutoSchema

schema = AutoSchema(api, OpenAPIConfig(title="My API", version="v1")).generate()
```

接口名固定为"模型名 + 动作", 列表用复数: `ArticlesList`, `ArticleCreate`, `ArticleRetrieve`,
`ArticlePartialUpdate`. 列表接口的筛选项会写进查询参数.

## 接口定义和客户端类型

接口定义 (OpenAPI 3.1) 是从代码导出的一个文件, 提交进仓库. 网页, iOS, Android, Flutter 的类型和请求代码都从它生成,
所以后端改了接口, 四个端在编译时就会报错.

```shell
python manage.py openapi                          # 导出到 openapi.json
python manage.py openapi --check                  # CI: 文件和代码不一致就失败
python manage.py openapi --breaking origin/main   # CI: 和主干比, 有破坏性变更就失败 (需要 oasdiff)
```

| 端 | 生成器 | 命令 |
|---|---|---|
| 网页 (TypeScript) | [Orval](https://orval.dev) | `orval --input openapi.json --output src/api.ts --client fetch` |
| iOS (Swift) | [Swift OpenAPI Generator](https://github.com/apple/swift-openapi-generator) | 配置里写 `namingStrategy: idiomatic` |
| Android (Kotlin) | [OpenAPI Generator](https://openapi-generator.tech) | `openapi-generator generate -i openapi.json -g kotlin -o api` |
| Flutter (Dart) | OpenAPI Generator | `openapi-generator generate -i openapi.json -g dart -o api` |

为了让四个生成器都能生成出干净的代码, 导出时强制几条规则, 不符合就报错:

- **接口名唯一**. 资源接口取自视图类名 (`ArticleList` 的列表是 `ArticlesList`), 业务接口取自函数名 (`upload_params` 是 `UploadParams`).
  客户端里的方法名就是它
- **每个接口都声明返回类型**, 类型是 Pydantic 模型. 不声明的话客户端拿到的是没有类型的对象
- **一个字段只有一种类型**, 可以再加 `None`. `str | int`, `dict | list` 这样的写法会被拒绝: Dart 生成不出合法的代码,
  Kotlin 和 Swift 生成的是包装类型. 需要两种形态时拆成两个字段
- 字段按模型里声明的顺序出现, 客户端里构造函数的参数也是这个顺序

破坏性变更由 [oasdiff](https://github.com/oasdiff/oasdiff) 判定: 删接口, 删响应字段, 改类型, 新增必填的请求字段等.
新增可选字段, 新增接口不算.

## 验证工具

`railguns.testing` 用来证明接口的行为没有变. 升级框架, 换库, 重写接口之前先录一份快照, 改完再跑.

```python
from railguns.testing import access_matrix, check_snapshot, serializer_contract


class ContractTests(TransactionTestCase):
    def test_access(self):
        matrix = access_matrix(api, {"anonymous": {}, "staff": {"Authorization": "Bearer ..."}})
        check_snapshot(self, "tests/snapshots/access.json", matrix)

    def test_fields(self):
        check_snapshot(self, "tests/snapshots/fields.json", serializer_contract(serializers))
```

| 工具 | 作用 |
|---|---|
| `access_matrix` | 每条路由用每种身份请求一次, 得到状态码矩阵. 路径参数取 1, 只能取某几个值的取第一个 |
| `serializer_contract` | 每个序列化器字段的类型, 是否必填, 是否只读 |
| `ParityTestCase` | 迁移期间新旧两套实现逐个请求比对响应 |
| `check_snapshot` | 和快照文件比对. `UPDATE_SNAPSHOTS=1` 时改为写入 |
| `block_external_network` | 测试里只放行本机的数据库和缓存 |
| `isolated_caches` | 每次运行用独立的缓存前缀 |

处理函数在引擎的线程里用自己的数据库连接. 测试里的数据要真的提交才看得到:
用 `TransactionTestCase`, 并且 `TestClient(api, share_db_connection=False)`.

## 配置

| 配置 | 用途 |
|---|---|
| `RAILGUNS_LOGIN_PROFILE` | 登录时附带返回的用户资料, 函数的路径. 可选 |
| `RAILGUNS_FOREIGN_KEY_APPS` | 允许用外键的应用标签 (app label) 列表, 这些应用的模型不做 `railguns.E003` 检查. 默认空. 不是字符串列表或应用没有安装时报 `railguns.E004` |
| `API_VERSION` | 后台上传控件拼接口地址用 |
| `BUCKET_MEDIA` / `BUCKET_STATIC` / `BUCKET_CLOUD` | 三个存储桶的名字 |
| `MEDIA_URL` / `STATIC_URL` / `CLOUD_URL` | 三个桶对应的上传地址 |
| `CLOUD_STORAGE_ID` / `CLOUD_STORAGE_SECRET` / `CLOUD_STORAGE_REGION` / `CLOUD_STORAGE_DOMAIN_NAME` | 对象存储的凭证, 区域, 域名 |
| `REST_FRAMEWORK["PAGE_SIZE"]` | 每页条数, 不配置为 20 |

### 日志

```python
from railguns.conf import LOGGING
```

访问日志由引擎在 Rust 里写到标准输出, 每个请求一行 JSON, railguns 启动时自动打开, 不用配置:

```json
{"ts":1795344954.612,"method":"GET","path":"/articles/7","status":200,"ms":0.4}
```

这份 `LOGGING` 把 Python 的 `django.server` 调到只记错误. 经过 Python 的 logging 记访问日志, 空接口的吞吐只剩三成;
在 Rust 里写是关掉时的 97%. 未处理的异常仍然记到 `django.request`.

## 关于引擎

- 接口路由不走 Django 的 `urlpatterns`, 用 `api.get(...)` / `api.post(...)` 注册. `railguns/urls.py` 里集中列出库提供的接口
- 路径末尾的斜杠默认被去掉: 注册的是 `/upload-params/{cloud}`, 带斜杠的请求会多一次重定向
- 依赖引擎内部细节的代码全部在 `rest_framework/_bolt.py`, 升级引擎时只需要核对这一个文件. 版本超出核对过的范围时启动会有警告

## 开发

```shell
uv sync --extra test
uv run --no-sync pytest -q -p no:cacheprovider --create-db
```

`tests/` 是一个最小的项目 (`tests/app`), 用 pytest 和 pytest-django 运行. 需要一个 PostgreSQL, 默认连本机 5432 端口,
用当前系统用户:

```shell
DB_HOST=... DB_PORT=... DB_USER=... DB_PASSWORD=... uv run --no-sync pytest -q -p no:cacheprovider --create-db
```

交付前在本地跑这三项检查, 都要零问题:

```shell
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uvx ty check
```

发布前检查装好的包: 打出 wheel, 和 freeman 一起装进一个新的虚拟环境, 用装好的包跑一遍测试. 少打包了文件 (比如迁移)
这里就会失败. freeman 从 `../freeman` 复制出来构建 (要几分钟), 也可以 `FREEMAN=path/to/freeman.whl` 指定 wheel:

```shell
sh scripts/check_wheel.sh
```

`tests/test_packaging.py` 在每次跑测试时检查 wheel 里有迁移和管理命令.

## License

RailgunS is released under the MIT license. [See LICENSE](https://github.com/nyssance/railguns/blob/main/LICENSE) for details.

[pyproject.toml] https://packaging.python.org/en/latest/guides/writing-pyproject-toml/
