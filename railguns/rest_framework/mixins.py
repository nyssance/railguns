from collections import OrderedDict
import datetime

from django.utils.timezone import localtime
from rest_framework import serializers
from rest_framework.response import Response


class IdStrMixin(serializers.Serializer):
    id_str = serializers.SerializerMethodField()

    def get_id_str(self, obj):
        return str(obj.id)


class ImageUrlsMixin(serializers.Serializer):
    images = serializers.SerializerMethodField()

    def get_images(self, obj):
        data = []
        if obj.image_urls.strip() != '':
            data = [{'url': item.strip(), 'uri': item.strip()} for item in obj.image_urls.split('\n')]
        return OrderedDict([('count', len(data)), ('next', None), ('previous', None), ('results', data)])


class TagsMixin(serializers.Serializer):
    tags = serializers.SerializerMethodField()

    def get_tags(self, obj):
        data = []
        for item in obj.tags.strip().split('#'):
            if item.strip() != '':
                data.append({'name': item.strip()})
        return OrderedDict([('count', len(data)), ('next', None), ('previous', None), ('results', data)])


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


class StartDateMixin(serializers.Serializer):
    start_date = serializers.SerializerMethodField()

    def get_start_date(self, obj):
        return localtime(obj.start_time).strftime('%Y-%m-%d')


class EndDateMixin(serializers.Serializer):
    end_date = serializers.SerializerMethodField()

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
