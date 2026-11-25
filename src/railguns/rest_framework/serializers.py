from pydantic import BaseModel


class DownloadUrlSerializer(BaseModel):
    """下载地址."""

    url: str


class UploadParamsSerializer(BaseModel):
    """上传参数: 上传的地址和表单字段."""

    endpoint: str
    params: dict[str, str]


class UploadRequest(BaseModel):
    """获取上传参数的请求."""

    filename: str
    bucket: str = ""
    expiration: int = 24 * 365 * 50
    content_encoding: str = ""
    cache_control: str = ""


class Image(BaseModel):
    """一张图片."""

    uri: str


class ImageList(BaseModel):
    """ImagesFieldMixin.get_images 的返回类型."""

    count: int
    data: list[Image]
