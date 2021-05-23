import datetime

from django.contrib.auth import login as auth_login
from django.contrib.auth.hashers import make_password
from django.utils.timezone import localtime
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import Serializer
from rest_framework_simplejwt.tokens import SlidingToken

from .schemas.openapi import AutoSchema
from .utils import get_nested_list


class SchemaMixin:
    schema = AutoSchema()


class ModelMixin:

    def get_model(self):
        return self.serializer_class.Meta.model


# Serializer Mixin
class PasswordFieldMixin(Serializer):
    password = CharField(style={'input_type': 'password'}, min_length=6, max_length=128, write_only=True)

    # SO https://stackoverflow.com/questions/29746584/django-rest-framework-create-user-with-password
    def validate_password(self, value):
        return make_password(value)


class TokenFieldMixin(Serializer):
    token = SerializerMethodField()

    def get_token(self, obj):
        request = self.context.get('request')
        if request:
            auth_login(request, obj)  # 主要为了记录last_login的, 其他的作用待研究
        else:
            print('request is None, 请在代码手动传入, 否则无法自动登录')
        return str(SlidingToken.for_user(request.user))


class ImagesFieldMixin(Serializer):
    images = SerializerMethodField()

    def get_images(self, obj):
        if hasattr(obj, 'images'):
            return get_nested_list([{'uri': item.strip()} for item in obj.images.split('\n') if item.strip()])
        else:
            return '👈⚠️️字段不存在，请去除。'


class TagsFieldMixin(Serializer):
    tags = SerializerMethodField()

    def get_tags(self, obj):
        if hasattr(obj, 'tags'):
            return [item.strip() for item in obj.tags.split('#') if item.strip()]
        else:
            return '👈⚠️️字段不存在，请去除。'


class StartDateFieldMixin(Serializer):
    start_date = SerializerMethodField(read_only=True)

    def get_start_date(self, obj):
        return localtime(obj.start_time).strftime('%Y-%m-%d')


class EndDateFieldMixin(Serializer):
    end_date = SerializerMethodField(read_only=True)

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


# View Mixin
class OwnerMixin:

    def pre_save(self, obj):
        obj.user_id = self.request.user.id
