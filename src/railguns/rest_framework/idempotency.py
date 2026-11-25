"""幂等的写入, 按 IETF 的 Idempotency-Key 草案 (draft-ietf-httpapi-idempotency-key-header).

客户端在 POST 上带 Idempotency-Key 头, 网络超时或重复点击时用同一个键重试, 数据只写一次:

- 第一次: 照常处理, 响应 (状态码和响应体) 连同请求的指纹 (方法, 路径, 请求体) 存下来, 按用户隔离.
- 同一个键, 同样的请求: 直接返回存下的响应, 不再处理.
- 同一个键, 不同的请求: 422.
- 同一个键的第一次请求还没处理完: 409.

资源接口的创建动作自动支持, 不用声明. 业务接口在注册时打开, 处理函数照常写:

    api.post("/orders", idempotent=True, **PRIVATE)(create_order)

    def create_order(request, data: OrderInput) -> Order:
        return run(services.create_order, actor(request), data)

约定:

- 键要登录才能用: 键按用户隔离, 未登录的请求带了键是 401.
- 带键的请求, 整个处理函数在一个数据库事务里执行, 存下的是处理函数最后返回的响应. 所以 run 之后还可以
  接着处理 (比如签发令牌). 键和这次请求写入的数据一起提交; 请求失败 (业务错误, 异常) 时全部回滚, 什么都不留下,
  同一个键可以重试. 数据库以外的副作用 (缓存, 短信) 不随事务回滚, 和不带键时一样.
- 键保留 24 小时 (TTL). 过期的键当作没用过; 定时运行 manage.py clearidempotencykeys 删掉过期的行.
"""

import hashlib
from datetime import timedelta
from functools import wraps
from inspect import get_annotations, signature
from typing import Any, get_type_hints
lazy from collections.abc import Callable

from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, connections, router, transaction
from django.utils import timezone
from freeman.exceptions import HTTPException
from freeman.responses import Response
from pydantic import TypeAdapter
lazy from freeman import Request

lazy from railguns.models import IdempotencyKey  # 模型在应用注册好之后才能导入, 用到时才导入

from .permissions import get_user_id

HEADER = "idempotency-key"
TTL = timedelta(hours=24)
MAX_LENGTH = 255
# 接口文档里的请求头参数
PARAMETER = {
    "name": "Idempotency-Key",
    "in": "header",
    "required": False,
    "description": "幂等键. 重试时带同一个值, 只处理一次; 24 小时内有效",
    "schema": {"type": "string", "maxLength": MAX_LENGTH},
}


def error(status_code: int, code: str, detail: str) -> HTTPException:
    """业务错误的异常, 响应体是 {"code": ..., "detail": ...}.

    Returns:
        要抛出的 HTTPException.

    """
    return HTTPException(status_code=status_code, detail={"code": code, "detail": detail})


def parse(value: str) -> str:
    """头的值. 草案里它是结构化字段的字符串 ("..."), 也接受不带引号的写法.

    Returns:
        去掉引号的键.

    Raises:
        error: 键不是 1 到 MAX_LENGTH 个可见的 ASCII 字符 (400).

    """
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        value = value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if not value or len(value) > MAX_LENGTH or not value.isascii() or not value.isprintable():
        raise error(400, "invalid_idempotency_key", f"Idempotency-Key 必须是 1 到 {MAX_LENGTH} 个可见的 ASCII 字符。")
    return value


class Claim:
    """一个带了幂等键的请求: 谁, 哪个键, 请求的指纹, 以及响应怎么编码."""

    def __init__(self, request: Request, adapter: TypeAdapter, status_code: int) -> None:
        """从请求里取出用户, 键和指纹.

        Raises:
            error: 没有登录 (401).

        """
        user_id = get_user_id(request)
        if user_id is None:
            raise error(401, "not_authenticated", "使用 Idempotency-Key 需要登录。")
        self.user_id = int(user_id)
        self.key = parse(request.headers[HEADER])
        digest = hashlib.sha256(f"{request.method}\n{request.path}\n".encode())
        digest.update(request.body or b"")
        self.fingerprint = digest.hexdigest()
        self.adapter = adapter
        self.status_code = status_code

    @classmethod
    def of(cls, request: Request, adapter: TypeAdapter, status_code: int) -> Claim | None:
        """请求带了 Idempotency-Key 时的 Claim, 否则 None: 和以前完全一样处理.

        Returns:
            Claim, 没带键时是 None.

        """
        return cls(request, adapter, status_code) if HEADER in request.headers else None

    def atomic(self, work: Callable[[], Any]) -> Response:
        """同步: 在一个事务里检查键, 执行 work, 存下响应. work 的写入和键在同一个连接, 同一个事务.

        work 是整个处理函数, 和键在同一个线程里执行, 所以它的查询都在这个事务里.

        Returns:
            要发出的响应.

        """
        with transaction.atomic(using=router.db_for_write(IdempotencyKey)):
            return self.once(work)

    def once(self, work: Callable[[], Any]) -> Response:
        """检查键, 执行 work, 存下响应. 调用时必须已经在事务里 (见 atomic).

        1. 试着拿这个键的事务级咨询锁. 拿不到说明同一个键的请求正在处理: 409. 锁随事务结束释放, 进程崩溃也一样
        2. 键用过并且没过期: 指纹不同是 422, 相同就返回存下的响应
        3. 执行 work, 编码响应, 插入键. 万一两个事务都走到这一步 (锁的哈希碰撞), 唯一约束让后提交的那个失败回滚

        Returns:
            要发出的响应: 存下的, 或者这次执行的.

        Raises:
            error: 同一个键的请求正在处理 (409), 或者键已经用于另一个请求 (422).

        """
        alias = router.db_for_write(IdempotencyKey)
        with connections[alias].cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_xact_lock(hashtextextended(%s, 0))", [f"{self.user_id}:{self.key}"])
            if not cursor.fetchone()[0]:
                raise error(409, "idempotency_key_in_use", "使用这个 Idempotency-Key 的请求还在处理中。")
        keys = IdempotencyKey.objects.using(alias)
        found = keys.filter(user_id=self.user_id, key=self.key).first()
        if found is not None and found.created_time < timezone.now() - TTL:
            found.delete()
            found = None
        if found is not None:
            if found.fingerprint != self.fingerprint:
                raise error(422, "idempotency_key_reused", "这个 Idempotency-Key 已经用于另一个请求。")
            return Response(content=bytes(found.body), status_code=found.status_code, media_type="application/json")
        status_code, body = self.encode(work())
        try:
            with transaction.atomic(using=alias):
                keys.create(
                    user_id=self.user_id, key=self.key, fingerprint=self.fingerprint, status_code=status_code, body=body
                )
        except IntegrityError as exc:
            raise error(409, "idempotency_key_in_use", "使用这个 Idempotency-Key 的请求还在处理中。") from exc
        return Response(content=body, status_code=status_code, media_type="application/json")

    def encode(self, result: object) -> tuple[int, bytes]:
        """处理函数的返回值编码成 (状态码, 响应体). 已经编好的 Response 原样存下, 其余按返回类型校验再编码.

        Returns:
            (状态码, 响应体).

        """
        if isinstance(result, Response) and isinstance(result.content, bytes):
            return result.status_code, result.content
        return self.status_code, self.adapter.dump_json(self.adapter.validate_python(result, from_attributes=True))


def idempotent(handler: Callable[..., object], status_code: int) -> Callable[..., object]:
    """带幂等键时, 整个处理函数在键的事务里执行, 存下它最后返回的响应.

    由 API.post(idempotent=True) 调用, 资源接口的创建动作由 generics 调用.

    Returns:
        包装后的处理函数, 注解和 handler 相同.

    Raises:
        ImproperlyConfigured: 处理函数没有 request 参数.

    """
    parameters = signature(handler).parameters
    if "request" not in parameters:
        msg = f"幂等的接口 {getattr(handler, "__name__", handler)} 必须有 request 参数."
        raise ImproperlyConfigured(msg)
    adapter = TypeAdapter(get_type_hints(handler).get("return", Any))

    @wraps(handler)
    def wrapper(*args: object, **kwargs: object) -> object:
        request = signature(handler).bind(*args, **kwargs).arguments["request"]
        claim = Claim.of(request, adapter, status_code)
        if claim is None:
            return handler(*args, **kwargs)
        return claim.atomic(lambda: handler(*args, **kwargs))

    wrapper.__annotations__ = get_annotations(handler)  # wraps 只复制 __annotate__, 手动设的 __annotations__ 会丢
    wrapper.railguns_idempotent = True
    return wrapper
