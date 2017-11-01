from rest_framework.generics import CreateAPIView, ListAPIView, ListCreateAPIView, RetrieveAPIView, RetrieveUpdateAPIView

from . import mixins


class CreateAPI(mixins.ModelMixin, CreateAPIView):
    """创建 API"""
    def get_queryset(self):
        return self.get_model().objects.all()

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id,
                        username=self.request.user.username,
                        user_image_uris=self.request.user.image_uris)


class ListAPI(mixins.ModelMixin, ListAPIView):
    """列表 API"""
    def get_queryset(self):
        return self.get_model().objects.filter(is_active=True)


class ListCreateAPI(mixins.ModelMixin, ListCreateAPIView):
    """列表 & 创建 API"""
    def get_queryset(self):
        if self.request.method == 'GET':
            return self.get_model().objects.filter(is_active=True)
        return self.get_model().objects.all()

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id,
                        username=self.request.user.username,
                        user_image_uris=self.request.user.image_uris)


class RetrieveAPI(mixins.ModelMixin, RetrieveAPIView):
    """详情 API"""
    def get_queryset(self):
        return self.get_model().objects.filter(is_active=True)


class RetrieveUpdateAPI(mixins.ModelMixin, mixins.PutToPatchMixin, RetrieveUpdateAPIView):
    """详情 & 更新 API"""
    def get_queryset(self):
        if self.request.method == 'GET':
            return self.get_model().objects.filter(is_active=True)
        return self.get_model().objects.all()


class OwnerListAPI(mixins.ModelMixin, ListAPIView):
    """拥有者 : 列表 API"""
    def get_queryset(self):
        return self.get_model().objects.filter(user_id=self.kwargs[self.lookup_field], is_active=True)
