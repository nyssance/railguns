import datetime

from django.utils.timezone import localtime
from rest_framework.fields import SerializerMethodField
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from .utils import get_nested_list


class ModelMixin(object):

    def get_model(self):
        return self.serializer_class.Meta.model


class IdStrMixin(Serializer):
    id_str = SerializerMethodField()

    def get_id_str(self, obj):
        return str(obj.id)


class ImagesMixin(Serializer):
    images = SerializerMethodField()

    def get_images(self, obj):
        data = []
        if hasattr(obj, 'images'):
            data = [{'uri': item.strip()} for item in obj.images.strip().split('\n')]
        else:
            pass
        return get_nested_list(data)


class TagsMixin(Serializer):
    tags = SerializerMethodField()

    def get_tags(self, obj):
        data = []
        if hasattr(obj, 'tags'):
            for item in obj.tags.strip().split('#'):
                if item.strip():
                    data.append({'name': item.strip()})
        else:
            pass
        return get_nested_list(data)


class OwnerMixin(object):

    def pre_save(self, obj):
        obj.user_id = self.request.user.id


class PutToPatchMixin(object):

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class PutToPatchApiViewMixin(object):

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)


class StartDateMixin(Serializer):
    start_date = SerializerMethodField()

    def get_start_date(self, obj):
        return localtime(obj.start_time).strftime('%Y-%m-%d')


class EndDateMixin(Serializer):
    end_date = SerializerMethodField()

    def get_end_date(self, obj):
        if obj.period <= 0:
            return ''
        else:
            return self.get_date_after_period(localtime(obj.start_time), obj.period)

    def get_date_after_period(self, date, period):
        days = period
        if period >= 0:
            days = period - 1
        date_time = date + datetime.timedelta(days=days)
        return date_time.strftime('%Y-%m-%d')
