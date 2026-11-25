"""业务错误.

在 services 里直接抛, 接口层统一转成响应:

    {"code": "insufficient_balance", "detail": "余额不足"}
    {"code": "invalid", "detail": "...", "fields": [{"loc": ["email"], "msg": "...", "type": "invalid"}]}

code 给程序判断, detail 给人看, fields 只在有字段错误时出现. 不要在 services 里拼响应或抛 HTTPException,
业务代码不应该知道自己是被接口调用的.

Django 的 ValidationError (full_clean() 抛出的) 不用转换, 经过 run 时就是 400, 带 fields.
要自己的 code 时: raise BusinessError.from_validation(exc, code="invalid_account").
"""

import logging

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError

logger = logging.getLogger("django.request")


def report(name: str) -> None:
    """把正在处理的异常记到 django.request 日志, 管理员告警邮件走的就是这个日志. 在 except 里调用.

    Bolt 自己处理未捕获的异常时不经过 Django 的请求日志, 不记的话线上出 500 没有人会收到通知.
    """
    logger.error("Internal Server Error: %s", name, exc_info=True, extra={"status_code": 500})


def field_errors(exc: ValidationError) -> list[dict]:
    """ValidationError 的每一条错误: {"loc", "msg", "type"}. loc 是字段名, 和整个对象有关的错误 loc 为空.

    Returns:
        错误的列表.

    """
    if not hasattr(exc, "error_dict"):
        return [
            {"loc": [], "msg": message, "type": error.code or "invalid"}
            for error in exc.error_list
            for message in error
        ]
    return [
        {"loc": [] if name == NON_FIELD_ERRORS else [str(name)], "msg": message, "type": error.code or "invalid"}
        for name, errors in exc.error_dict.items()
        for error in errors
        for message in error
    ]


class BusinessError(Exception):
    """业务错误的基类: 400, code 是 invalid."""

    status_code = 400
    code = "invalid"

    def __init__(self, detail: str = "", code: str | None = None, *, fields: list[dict] | None = None) -> None:
        """参数: detail 给人看, code 不传时用类的 code, fields 是字段错误 (见 field_errors)."""
        super().__init__(detail)
        self.detail = detail
        self.fields = fields or []
        if code:
            self.code = code

    @classmethod
    def from_validation(cls, exc: ValidationError, code: str | None = None) -> BusinessError:
        """Django 的 ValidationError 转成带 fields 的业务错误. detail 是所有错误信息连起来.

        Returns:
            业务错误.

        """
        return cls("; ".join(exc.messages), code, fields=field_errors(exc))


class NotFound(BusinessError):
    """找不到."""

    status_code = 404
    code = "not_found"


class PermissionDenied(BusinessError):
    """没有权限."""

    status_code = 403
    code = "permission_denied"


class Conflict(BusinessError):
    """状态不对, 比如重复提交, 已经审核过."""

    status_code = 409
    code = "conflict"


class TooManyRequests(BusinessError):
    """太频繁, 比如同一个号码 60 秒内只发一次验证码."""

    status_code = 429
    code = "rate_limited"


class BadGateway(BusinessError):
    """上游服务 (短信, 支付, 对象存储) 返回了失败."""

    status_code = 502
    code = "bad_gateway"


class ServiceUnavailable(BusinessError):
    """上游服务暂时不可用, 或者这个功能暂停了. 客户端可以稍后重试."""

    status_code = 503
    code = "service_unavailable"
