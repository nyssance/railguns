from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_jwt.serializers import jwt_encode_handler, jwt_payload_handler


class BaseModelSerializer(ModelSerializer):
    class Meta:
        exclude = ['updated_time', 'is_active']


class DownloadUrlSerializer(Serializer):
    url = CharField()


class UploadParamsSerializer(Serializer):
    key = CharField()
    AWSAccessKeyId = CharField()
    OSSAccessKeyId = CharField()
    acl = CharField()
    success_action_status = CharField()
    ContentType = CharField()
    policy = CharField()
    signature = CharField()
    ContentEncoding = CharField()
    domain = CharField()


class UserCreatedSerializer(ModelSerializer):
    token = SerializerMethodField()
    type = SerializerMethodField()

    class Meta:
        model = get_user_model()
        exclude = ['password', 'is_superuser', 'is_staff', 'date_joined', 'groups', 'user_permissions', 'is_active', 'last_login']

    def get_token(self, obj):
        return jwt_encode_handler(jwt_payload_handler(obj))

    def get_type(self, obj):
        USER_TYPE_CHOICES = [(0, '普通帐户'), (1, '企业帐户'), (2, '企业员工')]
        type_list = [i[1] for i in USER_TYPE_CHOICES if i[0] == obj.type]
        if len(type_list) != 0:
            return {'code': obj.type, 'message': type_list[0]}
        else:
            return {'code': 0, 'message': ''}


class UserPasswordSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['password']

    def validate_password(self, value):
        if len(value) < 6:
            raise ValidationError('password length must more than 6')
        return value
