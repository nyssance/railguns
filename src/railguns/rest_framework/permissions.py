"""对象级和列表级的权限."""

from typing import override

lazy from django.db.models import Model
lazy from freeman import Request

lazy from .generics import API

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


def get_user_id(request: Request) -> str | None:
    """从 token 上下文取用户 id, 不查库.

    Returns:
        用户 id, 未登录返回 None.

    """
    context = request.context
    return str(context["user_id"]) if context and context.get("user_id") else None


class BasePermission:
    """Bolt 的 guards 在 Rust 里按 token 声明判断, 拿不到数据库对象, 所以对象级权限放在 Python 侧.

    视图上写 object_permissions = [IsOwner()], 取到对象后检查; 列表级的写 request_permissions = [IsOwnerOnList()].
    """

    def has_object_permission(self, request: Request, view: API, obj: Model) -> bool:
        return True


class IsMe(BasePermission):  # 未登录用户id为None, 和任何对象都不相等
    """对象就是当前用户."""

    @override
    def has_object_permission(self, request: Request, view: API, obj: Model) -> bool:
        return str(obj.pk) == get_user_id(request)


class IsMeOrReadOnly(BasePermission):
    """对象是当前用户才能写, 谁都能读."""

    @override
    def has_object_permission(self, request: Request, view: API, obj: Model) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return str(obj.pk) == get_user_id(request)


class IsOwnerOnList(BasePermission):
    """列表的路径参数 (视图的 lookup_field) 是当前用户."""

    def has_permission(self, request: Request, view: API) -> bool:
        return view.lookup_field in request.params and str(request.params[view.lookup_field]) == get_user_id(request)


class IsOwner(BasePermission):
    """对象的 user_id 是当前用户."""

    @override
    def has_object_permission(self, request: Request, view: API, obj: Model) -> bool:
        return str(obj.user_id) == get_user_id(request)


class IsOwnerOrReadOnly(BasePermission):  # 为了不登录也能读, 不继承IsOwner
    """对象的 user_id 是当前用户才能写, 谁都能读."""

    @override
    def has_object_permission(self, request: Request, view: API, obj: Model) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return str(obj.user_id) == get_user_id(request)


class IsRelationOrReadOnly(BasePermission):
    """当前用户是关系的一方 (from_id 或 to_id) 才能写, 谁都能读."""

    @override
    def has_object_permission(self, request: Request, view: API, obj: Model) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return get_user_id(request) in {str(obj.from_id), str(obj.to_id)}


# https://www.django-rest-framework.org/api-guide/permissions/#examples
class BlacklistPermission(BasePermission):
    """请求的 IP 在黑名单里时拒绝."""

    def __init__(self, model: type[Model] | None = None) -> None:
        """model: 黑名单模型, 需要有 ip_addr 字段. 也可以在视图上写 blacklist_model."""
        self.model = model

    def has_permission(self, request: Request, view: API) -> bool:
        ip_addr = request.META["REMOTE_ADDR"]
        model = self.model or view.blacklist_model
        blacklisted = model.objects.filter(ip_addr=ip_addr).exists()
        return not blacklisted
