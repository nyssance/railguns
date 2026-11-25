"""业务函数: 不碰 request, 出错抛 railguns 的业务异常."""

from django.contrib.auth.models import AbstractUser

from railguns.rest_framework.errors import (
    BadGateway,
    Conflict,
    NotFound,
    PermissionDenied,
    ServiceUnavailable,
    TooManyRequests,
)
lazy from railguns.rest_framework.actions import Actor

from .models import Article
from .serializers import Done, Me, Profile, Publish, Published


def profile(user: AbstractUser) -> Profile:
    return Profile(username=user.get_username())


def publish(actor: Actor, pk: int, data: Publish) -> Published:
    article = Article.objects.filter(pk=pk).first()
    if article is None:
        msg = "没有这篇文章"
        raise NotFound(msg)
    if article.user_id != actor.user_id and not (isinstance(actor.user, AbstractUser) and actor.user.is_staff):
        msg = "不是你的文章"
        raise PermissionDenied(msg)
    article.title = data.title
    article.save()
    if data.title == "boom":  # 保存之后出错, 用来验证整个函数会回滚
        msg = "unexpected"
        raise RuntimeError(msg)
    if data.title == "dup":
        msg = "已经发布过"
        raise Conflict(msg, code="published")
    return Published(id=article.pk, title=article.title)


def whoami(actor: Actor) -> Me:
    return Me(user_id=actor.user_id, username=actor.user.get_username())


def titles(actor: Actor, offset: int, size: int) -> tuple[int, list[dict]]:
    queryset = Article.objects.filter(is_active=True).order_by("pk")
    return queryset.count(), list(queryset.values("id", "title")[offset : offset + size])


def check_article(actor: Actor, pk: int) -> Done:
    """full_clean() 的 ValidationError 不用转换, run 把它变成 400 带 fields.

    Returns:
        不出错时 ok.

    """
    Article(title="", score=0).full_clean(exclude=["user_id", "username"])
    return Done(ok=True)


def upstream(actor: Actor, status: int) -> Done:
    errors = {
        429: TooManyRequests("太频繁"),
        502: BadGateway("短信发送失败", code="sms_failed"),
        503: ServiceUnavailable("暂停"),
    }
    raise errors[status]
