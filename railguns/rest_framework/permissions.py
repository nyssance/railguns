from django.conf import settings
from ipware.ip import get_ip
from rest_framework import permissions


class IsUserSelf(permissions.IsAuthenticated):  # 未登录用户id为None, 没必要继承BasePermission, 用IsAuthenticated更安全

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsUserSelfOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user


class IsOwnerOnList(permissions.BasePermission):

    def has_permission(self, request, view):
        return int(view.kwargs.get('pk', 0)) == request.user.id


class IsOwnerOnUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return int(view.kwargs.get('pk', 0)) == request.user.id


class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class IsOwnerOrReadOnly(permissions.BasePermission):  # 为了不登录也能读, 不继承IsOwner

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == request.user.id


class IsRelationOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.from_id == request.user.id or obj.to_id == request.user.id


class IsWhiteIpOrIsAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        ip_addr = get_ip(request, right_most_proxy=True)
        white_ips = settings.WHITE_IPS
        if not request.user.is_authenticated():  # 如果没有登录.
            if ip_addr in white_ips:
                return True
        else:
            return request.user and request.user.is_authenticated()
