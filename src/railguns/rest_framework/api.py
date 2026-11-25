"""项目的接口入口.

项目里只用这个类, 不直接用引擎的 BoltAPI:

    from railguns.rest_framework.api import API

    api = API()

它把两件事定死:

- 错误只有一种格式: {"code", "detail", "fields"}. 不管是引擎在 Rust 里拒绝的 (未登录, 参数类型不对),
  还是请求体校验失败, 业务错误, 未处理的异常, 都是这一种.
- 资源接口只能用 generics 里的五个类 (CreateAPI, ListAPI, ListCreateAPI, RetrieveAPI, RetrieveUpdateAPI),
  通过 viewset 注册.
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any, TypedDict, Unpack, override

from freeman import BoltAPI
from freeman.error_handlers import code_detail
from freeman.postgres import close_pools

from . import idempotency
lazy from . import generics


class _Options(TypedDict, total=False):
    """BoltAPI 的构造参数, 除了 lifespan 和 error_formatter."""

    prefix: str
    trailing_slash: str
    namespace: str | None
    middleware: list[Any] | None
    django_middleware: bool | list[str] | dict[str, Any] | None
    enable_logging: bool
    logging_config: Any | None
    compression: Any | None
    openapi_config: Any | None
    validate_response: bool
    include_in_schema: bool | None


class _RouteOptions(TypedDict, total=False):
    """BoltAPI 注册路由的参数."""

    name: str | None
    response_model: Any
    status_code: int | None
    validate_response: bool | None
    guards: list[Any] | None
    auth: list[Any] | None
    tags: list[str] | None
    summary: str | None
    description: str | None
    response_class: type | None
    include_in_schema: bool | None
    deprecated: bool


type Decorator[F] = Callable[[F], F]


class API(BoltAPI):
    """项目的接口: 错误格式固定, 资源类用 viewset 注册, 进程退出时关掉原生连接池."""

    def __init__(
        self,
        *,
        lifespan: Callable[[BoltAPI], AbstractAsyncContextManager[None]] | None = None,
        **options: Unpack[_Options],
    ) -> None:
        """参数和 BoltAPI 一样, 只是不接受 error_formatter.

        Raises:
            TypeError: 传了 error_formatter.

        """
        if "error_formatter" in options:
            msg = "错误格式是固定的, 不接受 error_formatter."
            raise TypeError(msg)

        @asynccontextmanager
        async def with_pools(app: BoltAPI) -> AsyncGenerator[None]:
            """项目自己的 lifespan 照常执行. 进程退出时关掉原生连接池."""
            try:
                if lifespan is None:
                    yield
                else:
                    async with lifespan(app):
                        yield
            finally:
                await close_pools()

        super().__init__(error_formatter=code_detail, lifespan=with_pools, **options)

    @override
    def post(self, path: str, *, idempotent: bool = False, **options: Unpack[_RouteOptions]) -> Decorator[Callable]:
        """idempotent=True: 业务接口支持 Idempotency-Key, 见 idempotency. 资源接口的创建动作总是支持, 不用写.

        Returns:
            注册处理函数的装饰器.

        """
        register = super().post(path, **options)
        if not idempotent:
            return register
        status_code = options.get("status_code") or 200
        return lambda handler: register(idempotency.idempotent(handler, status_code))

    def viewset[T: type[generics.API]](self, path: str, **options: Unpack[_RouteOptions]) -> Decorator[T]:
        """注册一个资源类: @api.viewset("/articles", auth=..., guards=..., tags=[...]).

        Returns:
            注册资源类的装饰器, 原样返回这个类.

        """

        def register(cls: T) -> T:
            cls.register(self, path, **options)
            return cls

        return register
