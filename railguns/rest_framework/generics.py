from rest_framework import generics

from . import mixins
from .schemas.openapi import AutoSchema


class Base(mixins.ModelMixin):
    schema = AutoSchema()


class CreateAPI(Base, generics.CreateAPIView):
    """创建 API"""

    def get_queryset(self):
        return self.get_model().objects.all()

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id,
                        username=self.request.user.username,
                        user_avatar=self.request.user.avatar)


class ListAPI(Base, generics.ListAPIView):
    """列表 API"""

    def get_queryset(self):
        return self.get_model().objects.filter(is_active=True)


class ListCreateAPI(Base, generics.ListCreateAPIView):
    """列表 & 创建 API"""

    def get_queryset(self):
        if self.request.method == 'GET':
            return self.get_model().objects.filter(is_active=True)
        return self.get_model().objects.all()

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id,
                        username=self.request.user.username,
                        user_avatar=self.request.user.avatar)


class RetrieveAPI(Base, generics.RetrieveAPIView):
    """详情 API"""

    def get_queryset(self):
        return self.get_model().objects.filter(is_active=True)


class RetrieveUpdateAPI(Base, generics.RetrieveUpdateAPIView):
    """详情 & 更新 API"""

    def get_queryset(self):
        if self.request.method == 'GET':
            return self.get_model().objects.filter(is_active=True)
        return self.get_model().objects.all()
