import datetime as dt
import hashlib
import hmac
import json
import mimetypes
import uuid
from base64 import b64encode
from typing import TypedDict
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from freeman.auth import IsAuthenticated, JWTAuthentication, SessionAuthentication
from freeman.exceptions import HTTPException
lazy from django.contrib.auth.models import AbstractUser
lazy from freeman import Request

from railguns.django.db.utils import timestamp

from .auth import access_auth
from .serializers import DownloadUrlSerializer, UploadParamsSerializer
lazy from .serializers import UploadRequest

CLOUDS = ("aliyun", "aws")


def create_filename(filename: str) -> str:
    ext = filename.rsplit(".", maxsplit=1)[-1]
    return f"{uuid.uuid4().hex}.{ext}"


def sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def get_signing_key(key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = sign(("AWS4" + key).encode("utf-8"), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    return sign(k_service, "aws4_request")


def get_signature(msg: str, digestmod: str) -> str:
    if not settings.CLOUD_STORAGE_SECRET:
        msg = "CLOUD_STORAGE_SECRET 不存在"
        raise ImproperlyConfigured(msg)
    key = settings.CLOUD_STORAGE_SECRET.encode()
    return b64encode(hmac.new(key, msg.encode("utf-8"), digestmod).digest()).decode()


def get_params(
    cloud: str,
    region: str,
    bucket: str,
    filename: str,
    rename: bool,
    expiration: int,
    content_encoding: str,
    cache_control: str,
) -> dict[str, str | bytes]:
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    path = f"upload/{create_filename(filename)}" if rename else filename  # 是否重命名
    # 计算policy
    conditions: list[dict[str, str] | list[str]] = [
        {"bucket": bucket},
        ["starts-with", "$key", path.split("/")[0]],
        ["starts-with", "$Content-Type", content_type],
    ]
    policy_dict: dict[str, str | list[dict[str, str] | list[str]]] = {
        "expiration": (dt.datetime.now(dt.UTC) + dt.timedelta(hours=expiration)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "conditions": conditions,
    }
    # 时间相关
    t = dt.datetime.now(dt.UTC)
    amz_date = t.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = t.strftime("%Y%m%d")
    if cloud == "aws":
        conditions += [
            {"acl": "public-read"},
            {"success_action_status": "204"},
            {"x-amz-meta-uuid": "14365123651274"},
            {"x-amz-server-side-encryption": "AES256"},
            ["starts-with", "$x-amz-meta-tag", ""],
            {"x-amz-credential": f"{settings.CLOUD_STORAGE_ID}/{date_stamp}/{region}/s3/aws4_request"},
            {"x-amz-algorithm": "AWS4-HMAC-SHA256"},
            {"x-amz-date": amz_date},
        ]
        policy_dict["conditions"] = conditions
        # policy_dict["conditions"].append(["content-length-range", 1, 1024 * 1024 * 4])
    if content_encoding == "gzip":
        conditions.append(["starts-with", "$Content-Encoding", content_encoding])  # 就是 policy_dict["conditions"]
    string_to_sign = b64encode(json.dumps(policy_dict).encode("utf-8"))
    params: dict[str, str | bytes] = {"key": path, "Content-Type": content_type, "policy": string_to_sign}
    match cloud:
        case "aliyun":  # 阿里云
            signature = b64encode(
                hmac.new(settings.CLOUD_STORAGE_SECRET.encode("utf-8"), string_to_sign, hashlib.sha1).digest()
            )
            params.update({"OSSAccessKeyId": settings.CLOUD_STORAGE_ID, "signature": signature})
        case "aws":  # AWS https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-HTTPPOSTConstructPolicy.html
            for condition in conditions:
                if isinstance(condition, dict):
                    params.update(condition)
            params.pop("bucket")
            signing_key = get_signing_key(settings.CLOUD_STORAGE_SECRET, date_stamp, region, "s3")
            signature = hmac.new(signing_key, string_to_sign, hashlib.sha256).hexdigest()  # 16进制
            params.update({"x-amz-meta-tag": "", "x-amz-signature": signature})
    # 其他 Content-Encoding, Cache-Control
    if content_encoding == "gzip":
        params["Content-Encoding"] = content_encoding
    if cache_control:
        params["Cache-Control"] = cache_control
    return params


class _Access(TypedDict):
    """注册接口时的 auth 和 guards 参数."""

    auth: list[JWTAuthentication | SessionAuthentication]
    guards: list[IsAuthenticated]


# App 用访问令牌, 后台上传控件用登录会话
STORAGE: _Access = {"auth": [access_auth, SessionAuthentication()], "guards": [IsAuthenticated()]}


async def get_user(request: Request, cloud: str) -> AbstractUser:
    if cloud not in CLOUDS:
        raise HTTPException(status_code=404, detail="Not Found")
    user = await request.auser()
    if not user.is_authenticated or not user.is_active:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def download_url(request: Request, cloud: str, url: str = "") -> DownloadUrlSerializer:
    """获取下载地址.

    Returns:
        带签名的下载地址, 10 分钟有效.

    Raises:
        HTTPException: 云不支持 (404), 未登录 (401), 地址为空或者不是自己的桶 (400).

    """
    await get_user(request, cloud)
    # https://documents-domain-com.oss-cn-shanghai.aliyuncs.com/contract/001/Linux_Command3.pdf
    if not url:
        msg = "url不能为空"
        raise HTTPException(status_code=400, detail=msg)
    url_components = urlparse(url)
    bucket = url_components.netloc.replace(f".{settings.CLOUD_STORAGE_DOMAIN_NAME}", "")
    if url_components.scheme != "https" or bucket not in {
        settings.BUCKET_MEDIA,
        settings.BUCKET_STATIC,
        settings.BUCKET_CLOUD,
    }:
        raise HTTPException(status_code=400, detail="Invalid storage URL")  # 只给自己的桶签名
    expires = int(timestamp(dt.datetime.now().astimezone())) + 600  # 10分钟有效
    string_to_sign = f"GET\n\n\n{expires}\n/{bucket}{url_components.path}"  # 字符串
    signature = get_signature(string_to_sign, "sha1")
    return DownloadUrlSerializer(
        url=f"{url}?OSSAccessKeyId={settings.CLOUD_STORAGE_ID}&Expires={expires}&Signature={signature}"
    )


async def upload_params(request: Request, cloud: str, data: UploadRequest) -> UploadParamsSerializer:
    """获取上传参数.

    filename -- 文件名, 可含有路径
    expiration -- (可选)过期时间, 默认50年
    content_encoding -- (可选)默认不压缩
    cache_control -- (可选)默认没有

    Returns:
        上传的地址和表单字段.

    Raises:
        HTTPException: 云不支持 (404), 未登录 (401), 参数不对 (400), 非员工传到媒体以外的桶 (403).

    """
    user = await get_user(request, cloud)
    filename = data.filename
    if not filename:
        msg = "filename不能为空"
        raise HTTPException(status_code=400, detail=msg)
    bucket = data.bucket or settings.BUCKET_MEDIA
    expiration = data.expiration  # 过期时间
    content_encoding = data.content_encoding
    cache_control = data.cache_control
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
            raise HTTPException(status_code=400, detail="Invalid upload parameters")
    if bucket != settings.BUCKET_MEDIA and not user.is_staff:
        raise HTTPException(status_code=403, detail="Staff access required")
    params = get_params(
        cloud, settings.CLOUD_STORAGE_REGION, bucket, filename, rename, expiration, content_encoding, cache_control
    )
    fields = {key: value.decode() if isinstance(value, bytes) else value for key, value in params.items()}
    return UploadParamsSerializer(endpoint=endpoint, params=fields)
