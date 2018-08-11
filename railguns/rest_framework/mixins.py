import datetime

from django.utils.timezone import localtime
from rest_framework.fields import SerializerMethodField
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
        if hasattr(obj, 'images'):
            return get_nested_list([{'uri': item.strip()} for item in obj.images.split('\n') if item.strip()])
        else:
            return '👈⚠️️字段不存在，请去除。'


class TagsMixin(Serializer):
    tags = SerializerMethodField()

    def get_tags(self, obj):
        if hasattr(obj, 'tags'):
            return [item.strip() for item in obj.tags.split('#') if item.strip()]
        else:
            return '👈⚠️️字段不存在，请去除。'


class OwnerMixin(object):

    def pre_save(self, obj):
        obj.user_id = self.request.user.id


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
