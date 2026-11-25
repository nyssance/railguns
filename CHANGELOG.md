# RailgunS

## 0.300

引擎换成 Freeman, 并且把四件事定死. 不兼容 0.2.

### 变化

- 引擎从 Django-Bolt 换成 [Freeman](https://github.com/nyssance/freeman). 导入名从 `django_bolt` 变成 `freeman`
- 数据库只支持 PostgreSQL, 并且必须配连接池 (`OPTIONS["pool"]`). 不符合时系统检查报错 (`railguns.E001`, `railguns.E002`).
  MySQL 的可选依赖移除
- 项目的接口入口改用 `railguns.rest_framework.api.API`. 错误格式固定为 `{"code", "detail", "fields"}`, 不接受自定义
- 资源接口只用 Pydantic 模型: `serializer_class` 是响应, 新增的 `input_class` 是请求体. 原来基于 Bolt `Serializer` 的写法移除.
  主键和所有者字段不允许出现在 `input_class` 里
- 读 (列表, 详情) 改为由 Django 编译 SQL, 原生异步连接执行, 不经过 ORM 的线程池
- 列表读出的列按 `serializer_class` 里声明的顺序
- 创建成功返回 201
- 接口名改为取自视图类名, 原来取自模型名, 同一个模型有多个视图时会重名
- 页码只能是数字, `page=last` 移除
- `serializer_class` 的每个字段必须是模型的列, 或者计算字段, 否则启动报错. 以前模型上的 `@property` 在详情里能用,
  在列表里 500. 详情不再返回模型实例, 和列表用同一份代码建响应
- 有 `choices` 的模型字段做路径参数时, 只接受其中的值, 其余是 422 (以前查出一个空列表). 接口定义里是 enum
- 幂等的业务接口带键时, 整个处理函数在键的事务里执行, 存下它最后返回的响应 (以前存的是业务函数的返回值).
  `run` 之后可以接着处理; 不再要求业务函数是同步的
- `RAILGUNS_LOGIN_PROFILE` 指定的函数必须声明返回类型 (Pydantic 模型). 登录的响应类型 `LoginResult` 由它生成,
  不再是 `additionalProperties`. 响应的字段和以前一样, 资料和令牌在同一层. `auth.login` 改为 `auth.login_handler()` 生成
- `PAGE_SIZE`, `MAX_PAGE_SIZE` 移到 `pagination`, `generics` 里仍可导入
- 业务接口里 Django 的 `ValidationError` 不再是 500, 是 400 带 `fields`
- `ImagesFieldMixin.get_images` 返回 `ImageList`, 字段不存在时不再返回提示字符串
- 存储接口 (`upload-params`, `download-url`) 从类视图改成函数
- `mixins` 里只剩字段用的辅助方法. `ModelMixin`, `PermissionMixin`, `FilterMixin`, `SaveMixin`, `OwnerMixin` 移除, 它们的行为在资源类里
- `railguns.testing.contract` 的字段契约按 Pydantic 输出: `{type, required, computed}`
- 只支持 Django 6.1

### 新增

- `railguns.checks`: 数据库的系统检查. `INSTALLED_APPS` 里要有 `"railguns"`
- 模型不用外键: 项目的模型 (railguns 自己的, 以及不在 site-packages 里, 名字不是 `django.` 开头的应用) 声明了
  `ForeignKey` / `OneToOneField` / `ManyToManyField` 时系统检查报错 (`railguns.E003`), 指出模型和字段.
  从抽象基类继承的字段按声明它的基类算: `AbstractUser` 的 `groups`, `user_permissions` 是 Django 声明的, 不报.
  `RAILGUNS_FOREIGN_KEY_APPS` (应用标签列表, 默认空) 里的应用整个不检查, 别的应用里指向它们的外键照样报;
  这个配置不是字符串列表或有没安装的应用时报错 (`railguns.E004`)
  别的表的行用 id 列引用, 资源接口只输出列和计算字段
- `railguns.testing.runner.Runner`: 测试运行器, 删测试库之前先关掉连接池
- 访问日志默认由引擎在 Rust 里写到标准输出, 每个请求一行 JSON
- 登出: `POST /auth/logout` (这一次登录), `POST /auth/logout-all` (所有设备)
- `manage.py openapi`: 导出接口定义, `--check` 检查它和代码一致, `--breaking` 用 oasdiff 检查破坏性变更
- 导出时的规则: 接口名唯一, 每个接口声明返回类型, 一个字段只有一种类型. 用同一份定义实际生成并编译过
  TypeScript (Orval), Swift, Kotlin, Dart 四个端的客户端
- 列表接口的 `page` / `page_size` 和筛选参数写进接口定义
- 登录和刷新声明了返回类型 `LoginResult` / `TokenPair`
- 读更快: 一页只发一条语句 (总数是标量子查询); 编译好的 SQL 按请求的输入记在每个进程的 LRU 里 (4096 条),
  同样的请求不再编译; `serializer_class` 只有列时一页直接编码, 不逐行校验. 单进程实测列表 2,800 → 6,600 req/s,
  详情 4,100 → 12,400 req/s. 覆盖了 `get_queryset` / `filter_queryset` 的类每次都编译
- 创建更快: INSERT 由 Django 编译, `RETURNING` 响应要的列, 原生连接上一条语句, 不经过线程池; SQL 每个视图类编译一次.
  所有者字段 (`user_id`, `username`, `user_avatar`) 在同一条语句里从用户表读出 (`INSERT ... SELECT`), 不再经过 ORM 读用户.
  有 `pre_save` / `post_save` 接收者, 覆盖了 `save()`, 视图覆盖了 `perform_create` / `get_user`, 带 `Idempotency-Key` 时
  照旧走 ORM. 单进程顺序调用实测 `PostModel` 的创建 660 → 190 us
- 令牌有效, 但用户已删除或停用时, 创建是 401 (`not_authenticated`), 不写入. 以前是 500
- 创建和更新违反唯一约束时是 409: `{"code": "conflict", "fields": [{"loc": ["title"], "type": "unique", ...}]}`,
  认不出约束的字段时没有 `fields`. 以前是 500. 其他完整性错误 (非空, 检查约束等) 仍然是 500
- `pagination.Pagination`: 业务接口自己分页, 和资源接口的列表是同一份代码.
  返回类型是 `Page[T]` 时, 接口定义里自动带上分页参数
- 错误: `TooManyRequests` (429), `BadGateway` (502), `ServiceUnavailable` (503). `BusinessError` 可以带 `fields`,
  `BusinessError.from_validation(exc)` 把 `ValidationError` 转成 `{"code", "detail", "fields": [{"loc", "msg", "type"}]}`
- `auth.session(user)`: 用户资料加令牌, 和登录的响应一样
- `railguns.testing.matrix.sample_path` 按处理函数的参数类型取值, 只能取某几个值的路径参数取第一个
- `scripts/check_wheel.sh`: 打出 wheel, 装进新的虚拟环境, 用装好的包跑测试. `tests/test_packaging.py` 检查 wheel 里有迁移
- `Idempotency-Key` (IETF 草案): 资源接口的创建自动支持, 业务接口用 `api.post(..., idempotent=True)` 打开.
  键按用户隔离, 存在 `railguns_idempotencykey` 表 (要 `migrate`), 保留 24 小时,
  `manage.py clearidempotencykeys` 删掉过期的行. 接口定义里写明这个请求头

### 修复

- wheel 里没有 `railguns/migrations/0001_initial.py`: `.gitignore` 忽略了所有 `migrations/`, 打包也跟着忽略.
  装好的包 `migrate` 时建不出幂等键的表

## 0.202

接口层从 Django REST framework 换成 Django-Bolt. 文件名和类名保持不变, 方便对照.

### 变化

- `rest_framework/generics.py` 的五个类改为基于 Bolt 的视图, 方法都是异步的
- 认证改用 Bolt 的令牌: `POST /auth/login`, `POST /auth/refresh`. 原来的 `api/token/` 和 `api/token/refresh/` 不再提供
- 接口路由从 `urlpatterns` 移到 `railguns.urls.api`, 项目入口挂载一次
- 上传签名和下载签名的地址不再带末尾斜杠, 并且要挂在项目的接口前缀下
- 序列化器的字段 Mixin 不能再被继承, 改为调用其方法. `TokenFieldMixin` 和 `SchemaMixin` 移除
- 依赖改为版本范围: Django 6.0 到 6.1, Django-Bolt 0.13. MySQL 驱动移到可选依赖 `railguns[mysql]`

### 新增

- 业务接口的写法: `rest_framework/actions.py` (`run`, `actor`) 和 `rest_framework/errors.py`
- `railguns.testing`: 权限矩阵, 字段契约, 新旧比对, 快照
- `rest_framework/_bolt.py`: 集中所有依赖 Bolt 内部细节的代码
- 未处理的异常记到 `django.request` 日志, 资源接口和业务接口都覆盖
- `RAILGUNS_LOGIN_PROFILE`: 登录时附带返回的用户资料
- `railguns.conf.LOGGING`: 默认日志配置, 关掉 Bolt 的逐请求访问日志
- 仓库自带测试 (`tests/`), 在 Django 6.0 / 6.1, SQLite / MySQL 8.0.13 上通过

### 修复

- 写入接口先判断登录再校验参数
- 只读字段在进程刚启动时也不能被请求体修改
- 上传签名接口同时接受访问令牌和后台登录会话
- 上传签名和下载签名只接受 `aliyun` 和 `aws`, 下载签名只给自己的桶签
