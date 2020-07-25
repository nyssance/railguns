from django.conf import settings
from rest_framework import permissions


class IsMe(permissions.IsAuthenticated):  # 未登录用户id为None, 没必要继承BasePermission, 用IsAuthenticated更安全

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsMeOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user


class IsOwnerOnList(permissions.BasePermission):

    def has_permission(self, request, view):
        return view.lookup_field in view.kwargs and view.kwargs[view.lookup_field] == request.user.id


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


# https://www.django-rest-framework.org/api-guide/permissions/#examples
class BlacklistPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        ip_addr = request.META['REMOTE_ADDR']
        blacklisted = Blacklist.objects.filter(ip_addr=ip_addr).exists()
        return not blacklisted
