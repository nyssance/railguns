from rest_framework.fields import CharField
from rest_framework.serializers import Serializer


class DownloadUrlSerializer(Serializer):
    url = CharField(read_only=True)


class UploadParamsSerializer(Serializer):
    bucket = CharField(write_only=True)
    filename = CharField(write_only=True, required=True)
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
