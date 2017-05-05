from base64 import b64encode
import datetime
import hashlib
import hmac
from urllib.parse import urlparse, quote_plus

from django.conf import settings

from ..django.db.utils import timestamp


def oss_download_url(url):
    url_components = urlparse(url)
    bucket = url_components.netloc.replace('.{}'.format(settings.CLOUD_STORAGE_BASE_DOMAIN_NAME), '')
    expires = int(timestamp(datetime.datetime.now())) + 600  # 10分钟有效
    string_to_sign = 'GET\n\n\n{}\n/{}{}'.format(expires, bucket, url_components.path)  # 字符串
    if settings.CLOUD_SECRET_ACCESS_KEY:  # 如果有SECRET
        signature = b64encode(hmac.new(settings.CLOUD_SECRET_ACCESS_KEY.encode(), string_to_sign.encode(), hashlib.sha1).digest())
    params = {'url': '{}?OSSAccessKeyId={}&Expires={}&Signature={}'.format(url, settings.CLOUD_ACCESS_KEY_ID, expires, quote_plus(signature))}
    return params
