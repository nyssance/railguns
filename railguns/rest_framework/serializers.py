from django.contrib.auth import get_user_model
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_jwt.serializers import jwt_encode_handler, jwt_payload_handler


class DownloadUrlSerializer(Serializer):
    url = CharField(read_only=True)


class UploadParamsSerializer(Serializer):
    key = CharField(read_only=True)
    AWSAccessKeyId = CharField(read_only=True)
    OSSAccessKeyId = CharField(read_only=True)
    acl = CharField(read_only=True)
    success_action_status = CharField(read_only=True)
    ContentType = CharField(read_only=True)
    policy = CharField(read_only=True)
    signature = CharField(read_only=True)
    ContentEncoding = CharField(read_only=True)
    domain = CharField(read_only=True)


class UserCreatedSerializer(ModelSerializer):
    token = SerializerMethodField()
    type = SerializerMethodField()

    class Meta:
        model = get_user_model()
        exclude = [
            'password', 'is_superuser', 'is_staff', 'date_joined', 'groups', 'user_permissions', 'is_active',
            'last_login'
        ]

    def get_token(self, obj):
        return jwt_encode_handler(jwt_payload_handler(obj))

    def get_type(self, obj):
        USER_TYPES = [(0, '普通帐户'), (1, '企业帐户'), (2, '企业员工')]
        type_list = [i[1] for i in USER_TYPES if i[0] == obj.type]
        if len(type_list) > 0:
            return {'code': obj.type, 'message': type_list[0]}
        else:
            return {'code': 0, 'message': ''}


class UserPasswordSerializer(ModelSerializer):
    password = CharField(style={'input_type': 'password'}, min_length=6, max_length=128, write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['password']
