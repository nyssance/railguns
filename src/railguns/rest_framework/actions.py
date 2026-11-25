"""业务接口的写法.

资源接口 (增查改) 用 generics 里的五个类: CreateAPI, ListAPI, ListCreateAPI, RetrieveAPI, RetrieveUpdateAPI.
除此之外的接口都是业务接口, 固定分成两层:

    # api.py: 只做三件事, 认证 / 收参数 / 回结果
    def repay(request, data: RepayInput) -> RepayResult:
        return run(services.repay, actor(request), data)

    # services.py: 纯业务. 不碰 request, 不拼响应, 出错抛 errors 里的异常
    def repay(actor, data):
        order = Order.objects.select_for_update().get(pk=data.order_id)
        if order.user_id != actor.user_id and not actor.user.is_staff:
            raise PermissionDenied("不是你的订单")
        ...

这样业务函数可以脱离接口单独测试, 定时任务和管理命令也能直接调用.
"""

lazy from collections.abc import Callable

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import transaction
from freeman.exceptions import HTTPException
lazy from django.contrib.auth.base_user import AbstractBaseUser
lazy from freeman import Request

from .errors import BusinessError, report


class Actor:
    """当前操作人.

    user_id 从 token 上下文取, 不查库, 未登录时为 None. 需要用户的其他信息 (是否员工, 是否停用) 时用 user,
    它每次请求只查一次库. 不从 token 里读这些信息: token 签发之后用户的状态可能已经变了.
    """

    def __init__(self, user_id: int | None = None) -> None:
        """user_id 是 None 时是未登录的用户."""
        self.user_id = user_id
        self._user: AbstractBaseUser | AnonymousUser | None = None

    @property
    def is_authenticated(self) -> bool:
        """是否已登录.

        Returns:
            有 user_id 时为 True.

        """
        return self.user_id is not None

    @property
    def user(self) -> AbstractBaseUser | AnonymousUser:
        """用户, 每次请求只查一次库.

        Returns:
            用户, 未登录时是 AnonymousUser.

        """
        if self._user is None:
            self._user = get_user_model().objects.get(pk=self.user_id) if self.is_authenticated else AnonymousUser()
        return self._user


def actor(request: Request) -> Actor:
    """请求的操作人, 从 token 上下文取 user_id.

    Returns:
        操作人.

    """
    user_id = (request.context or {}).get("user_id")
    return Actor(int(user_id) if user_id else None)


def http_error(exc: BusinessError) -> HTTPException:
    """业务错误转成约定格式的响应. fields 放在 extra 里, 错误格式里它和 code, detail 并列.

    Returns:
        要抛出的异常.

    """
    extra = {"fields": exc.fields} if exc.fields else None
    return HTTPException(status_code=exc.status_code, detail={"code": exc.code, "detail": exc.detail}, extra=extra)


def run[R](service: Callable[..., R], *args: object, atomic: bool = True, **kwargs: object) -> R:
    """执行一个业务函数.

    - 直接在处理函数的线程里调用, 默认整个包在一个数据库事务里, 出错全部回滚. atomic=False 可以关掉
    - BusinessError 转成约定格式的响应. Django 的 ValidationError 是 400, 每个字段的错误在 fields 里
    - 其他异常记到 django.request 日志 (管理员告警邮件走的就是这个日志) 再原样抛出

    幂等的接口 (见 idempotency) 整个处理函数都在键的事务里, 这里的事务是其中的保存点, 不用另外声明.

    Returns:
        业务函数的返回值.

    Raises:
        http_error: BusinessError 和 ValidationError 转成的 HTTPException.
        HTTPException: 业务函数自己抛的, 原样抛出.

    """
    try:
        return (transaction.atomic(service) if atomic else service)(*args, **kwargs)
    except ValidationError as exc:
        raise http_error(BusinessError.from_validation(exc)) from exc
    except BusinessError as exc:
        raise http_error(exc) from exc
    except HTTPException:
        raise
    except Exception:
        report(getattr(service, "__qualname__", str(service)))
        raise
