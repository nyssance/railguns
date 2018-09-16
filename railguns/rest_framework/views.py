import datetime
import hashlib
import hmac
import mimetypes
import uuid
from base64 import b64encode
from urllib.parse import quote_plus, urlparse

from django.conf import settings
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from ..django.db.utils import timestamp
from .permissions import IsAuthenticatedOrWhitelist
from .serializers import DownloadUrlSerializer, UploadParamsSerializer


def create_filename(filename):
    ext = filename.split('.')[-1]
    return '{}.{}'.format(uuid.uuid4().hex, ext)


def get_signature(msg):
    if not settings.CLOUD_SS_SECRET:
        raise APIException('CLOUD_SS_SECRET 不存在')
    key = settings.CLOUD_SS_SECRET.encode()
    return b64encode(hmac.new(key, msg.encode(), hashlib.sha1).digest()).decode()


def get_params(cloud, bucket, filename, rename, expiration, content_encoding, cache_control):
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    path = 'upload/{}'.format(create_filename(filename)) if rename else filename  # 是否重命名
    # 计算policy
    policy_object = {
        'expiration':
        (datetime.datetime.utcnow() + datetime.timedelta(hours=expiration)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'conditions': [
            {
                'bucket': bucket
            },
            ['starts-with', '$key',
             path.split('/')[0]],  # https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-HTTPPOSTConstructPolicy.html
            ['starts-with', '$Content-Type', content_type]
        ]
    }
    if cloud in ['aws', 's3']:
        policy_object['conditions'].append({'acl': 'public-read'})
        policy_object['conditions'].append({'success_action_status': '201'})  # 官方文档漏掉了, 这个在这里和html里一定不能少
        policy_object['conditions'].append(['content-length-range', 1, 1024 * 1024 * 4])
    if content_encoding == 'gzip':
        policy_object['conditions'].append(['starts-with', '$Content-Encoding', content_encoding])
    policy = b64encode(json.dumps(policy_object).replace('\n', '').replace('\r', '').encode()).decode()
    signature = get_signature(policy)
    params = {'key': path, 'Content-Type': content_type, 'policy': policy, 'signature': signature}
    if cloud in ['aliyun', 'oss']:
        params['OSSAccessKeyId'] = settings.CLOUD_SS_ID
    elif cloud in ['aws', 's3']:
        params.update({'AWSAccessKeyId': settings.CLOUD_SS_ID, 'acl': 'public-read', 'success_action_status': '201'})
    if content_encoding == 'gzip':
        params['Content-Encoding'] = content_encoding
    if cache_control:
        params['Cache-Control'] = cache_control
    if bucket == settings.BUCKET_MEDIA:
        params['domain'] = settings.MEDIA_URL
    elif bucket == settings.BUCKET_STATIC:
        params['domain'] = settings.STATIC_URL
    elif bucket == settings.BUCKET_CLOUD:
        params['domain'] = settings.CLOUD_URL
    return params


@permission_classes([IsAuthenticatedOrWhitelist])
class DownloadUrlView(APIView):
    """
    获取下载地址
    """
    lookup_field = 'cloud'
    serializer_class = DownloadUrlSerializer

    def get(self, request, *args, **kwargs):
        url = request.GET.get(
            'url')  # https://documents-domain-com.oss-cn-shanghai.aliyuncs.com/contract/001/Linux_Command3.pdf
        if not url:
            raise ValidationError('url不能为空')
        url_components = urlparse(url)
        bucket = url_components.netloc.replace('.{}'.format(settings.CLOUD_SS_BASE_DOMAIN_NAME), '')
        expires = int(timestamp(datetime.datetime.now())) + 600  # 10分钟有效
        string_to_sign = 'GET\n\n\n{}\n/{}{}'.format(expires, bucket, url_components.path)  # 字符串
        signature = get_signature(string_to_sign)
        params = {
            'url': '{}?OSSAccessKeyId={}&Expires={}&Signature={}'.format(url, settings.CLOUD_SS_ID, expires, signature)
        }
        return Response(params)


@permission_classes([IsAuthenticatedOrWhitelist])
class UploadParamsView(APIView):
    """
    获取上传参数
    filename -- 文件名, 可含有路径
    expiration -- (可选)过期时间, 默认50年
    content_encoding -- (可选)默认不压缩
    cache_control -- (可选)默认没有
    """
    lookup_field = 'cloud'
    serializer_class = UploadParamsSerializer  # 加了只是为OpenAPI用, 不影响输出结果

    def post(self, request, *args, **kwargs):
        filename = request.data.get('filename')
        if not filename:
            raise ValidationError('filename不能为空')
        rename = False
        bucket = request.data.get('bucket', settings.BUCKET_MEDIA)
        if bucket == settings.BUCKET_STATIC:  # 传到static下的不修改大小写
            filename = filename.lower()
        elif bucket == settings.BUCKET_MEDIA:
            rename = True
        expiration = int(request.GET.get('expiration', 24 * 365 * 50))  # 过期时间
        content_encoding = request.GET.get('content_encoding', '')
        cache_control = request.GET.get('cache_control')
        params = get_params(
            kwargs.get(self.lookup_field), bucket, filename, rename, expiration, content_encoding, cache_control)
        return Response(params)
