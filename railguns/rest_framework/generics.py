from rest_framework import generics

from . import mixins


class CreateAPI(mixins.ModelMixin, generics.CreateAPIView):
    """创建 API"""

    def get_queryset(self):
        return self.get_model().objects.all()

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id,
                        username=self.request.user.username,
                        user_avatar=self.request.user.avatar)


class ListAPI(mixins.ModelMixin, generics.ListAPIView):
    """列表 API"""

    def get_queryset(self):
        return self.get_model().objects.filter(is_active=True)


class ListCreateAPI(mixins.ModelMixin, generics.ListCreateAPIView):
    """列表 & 创建 API"""

    def get_queryset(self):
        if self.request.method == 'GET':
            return self.get_model().objects.filter(is_active=True)
        return self.get_model().objects.all()

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id,
                        username=self.request.user.username,
                        user_avatar=self.request.user.avatar)


class RetrieveAPI(mixins.ModelMixin, generics.RetrieveAPIView):
    """详情 API"""

    def get_queryset(self):
        return self.get_model().objects.filter(is_active=True)


class RetrieveUpdateAPI(mixins.ModelMixin, generics.RetrieveUpdateAPIView):
    """详情 & 更新 API"""

    def get_queryset(self):
        if self.request.method == 'GET':
            return self.get_model().objects.filter(is_active=True)
        return self.get_model().objects.all()
