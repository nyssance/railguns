import datetime
import hashlib
import hmac
import mimetypes
import uuid
from base64 import b64encode
from urllib.parse import urlparse

from django.conf import settings
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from ..django.db.utils import timestamp
from .serializers import DownloadUrlSerializer, UploadParamsSerializer


def create_filename(filename):
    ext = filename.split('.')[-1]
    return f'{uuid.uuid4().hex}.{ext}'


def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signing_key(key, date_stamp, region, service):
    kDate = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = sign(kDate, region)
    kService = sign(kRegion, service)
    kSigning = sign(kService, 'aws4_request')
    return kSigning


def get_signature(msg, digestmod):
    if not settings.CLOUD_STORAGE_SECRET:
        raise APIException('CLOUD_STORAGE_SECRET 不存在')
    key = settings.CLOUD_STORAGE_SECRET.encode()
    return b64encode(hmac.new(key, msg.encode('utf-8'), digestmod).digest()).decode()


def get_params(cloud, region, bucket, filename, rename, expiration, content_encoding, cache_control):
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    path = f'upload/{create_filename(filename)}' if rename else filename  # 是否重命名
    # 计算policy
    conditions = [{
        'bucket': bucket
    }, ['starts-with', '$key', path.split('/')[0]], ['starts-with', '$Content-Type', content_type]]
    policy_dict = {
        'expiration':
            (datetime.datetime.utcnow() + datetime.timedelta(hours=expiration)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'conditions':
            conditions
    }
    # 时间相关
    t = datetime.datetime.utcnow()
    expire = t + datetime.timedelta(days=1)
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    if cloud == 'aws':
        conditions += [{
            'acl': 'public-read'
        }, {
            'success_action_status': '204'
        }, {
            'x-amz-meta-uuid': '14365123651274'
        }, {
            'x-amz-server-side-encryption': 'AES256'
        }, ['starts-with', '$x-amz-meta-tag', ''], {
            'x-amz-credential': f'{settings.CLOUD_STORAGE_ID}/{date_stamp}/{region}/s3/aws4_request'
        }, {
            'x-amz-algorithm': 'AWS4-HMAC-SHA256'
        }, {
            'x-amz-date': amz_date
        }]
        policy_dict['conditions'] = conditions
        # policy_dict['conditions'].append(['content-length-range', 1, 1024 * 1024 * 4])
    if content_encoding == 'gzip':
        policy_dict['conditions'].append(['starts-with', '$Content-Encoding', content_encoding])
    string_to_sign = b64encode(json.dumps(policy_dict).encode('utf-8'))
    #
    params = {'key': path, 'Content-Type': content_type, 'policy': string_to_sign}
    match cloud:
        case 'aliyun':  # 阿里云
            signature = b64encode(
                hmac.new(settings.CLOUD_STORAGE_SECRET.encode('utf-8'), string_to_sign, hashlib.sha1).digest())
            params.update({'OSSAccessKeyId': settings.CLOUD_STORAGE_ID, 'signature': signature})
        case 'aws':  # AWS https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-HTTPPOSTConstructPolicy.html
            for condition in conditions:
                if isinstance(condition, dict):
                    params.update(condition)
            params.pop('bucket')
            signing_key = get_signing_key(settings.CLOUD_STORAGE_SECRET, date_stamp, region, 's3')
            signature = hmac.new(signing_key, string_to_sign, hashlib.sha256).hexdigest()  # 16进制
            params.update({'x-amz-meta-tag': '', 'x-amz-signature': signature})
    # 其他 Content-Encoding, Cache-Control
    if content_encoding == 'gzip':
        params['Content-Encoding'] = content_encoding
    if cache_control:
        params['Cache-Control'] = cache_control
    return params


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
        bucket = url_components.netloc.replace(f'.{settings.CLOUD_STORAGE_DOMAIN_NAME}', '')
        expires = int(timestamp(datetime.datetime.now())) + 600  # 10分钟有效
        string_to_sign = f'GET\n\n\n{expires}\n/{bucket}{url_components.path}'  # 字符串
        signature = get_signature(string_to_sign, hashlib.sha1)
        params = {'url': f'{url}?OSSAccessKeyId={settings.CLOUD_STORAGE_ID}&Expires={expires}&Signature={signature}'}
        return Response(params)


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
        bucket = request.data.get('bucket', settings.BUCKET_MEDIA)
        expiration = int(request.data.get('expiration', 24 * 365 * 50))  # 过期时间
        content_encoding = request.data.get('content_encoding', '')
        cache_control = request.data.get('cache_control')
        rename = False
        match bucket:
            case settings.BUCKET_MEDIA:
                endpoint = settings.MEDIA_URL
                rename = True
            case settings.BUCKET_STATIC:  # 传到static下的不修改大小写
                endpoint = settings.STATIC_URL
                # filename = filename.lower()
            case settings.BUCKET_CLOUD:
                endpoint = settings.CLOUD_URL
            case _:
                endpoint = ''
        params = get_params(kwargs.get(self.lookup_field), settings.CLOUD_STORAGE_REGION, bucket, filename, rename,
                            expiration, content_encoding, cache_control)
        return Response({'endpoint': endpoint, 'params': params})
