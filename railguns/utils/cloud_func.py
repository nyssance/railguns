from base64 import b64encode
import datetime
import hashlib
import hmac
import os
import subprocess
from urllib.parse import urlparse, quote_plus

from django.conf import settings

from ..django.db.utils import timestamp


def oss_download_url(url):
    url_components = urlparse(url)
    bucket = url_components.netloc.replace('.{}'.format(settings.CLOUD_STORAGE_BASE_DOMAIN_NAME), '')
    expires = int(timestamp(datetime.datetime.now())) + 600  # 10分钟有效.
    string_to_sign = 'GET\n\n\n{}\n/{}{}'.format(expires, bucket, url_components.path)  # 字符串.
    if settings.CLOUD_SECRET_ACCESS_KEY:  # 如果有SECRET.
        signature = b64encode(hmac.new(settings.CLOUD_SECRET_ACCESS_KEY.encode(), string_to_sign.encode(), hashlib.sha1).digest())
    else:
        signature_alg = os.path.join(settings.BASE_DIR, settings.CLOUD_SIGNATURE_FILE)
        signature = subprocess.check_output('{} --policy "{}"'.format(signature_alg, string_to_sign), shell=True).strip()  # 因为有换行符, 引号引起来.
    params = {'url': '{}?OSSAccessKeyId={}&Expires={}&Signature={}'.format(url, settings.CLOUD_ACCESS_KEY_ID, expires, quote_plus(signature))}
    return params
