"""序列化器里常用的派生字段.

在 Pydantic 模型的 computed_field 里调用:

@computed_field
@property
def image_list(self) -> ImageList:
    return ImagesFieldMixin().get_images(self)
"""

import datetime as dt
from typing import Protocol

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.utils.timezone import localtime

from .serializers import Image, ImageList


class _HasImages(Protocol):
    images: str  # 一行一个地址


class _HasTags(Protocol):
    tags: str  # # 分隔


class _HasStartTime(Protocol):
    start_time: dt.datetime


class _HasPeriod(_HasStartTime, Protocol):
    period: int  # 天数


class PasswordFieldMixin:
    """校验密码的长度, 存成哈希."""

    # SO https://stackoverflow.com/questions/29746584/django-rest-framework-create-user-with-password
    @staticmethod
    def validate_password(value: str) -> str:
        if not 6 <= len(value) <= 128:  # 原来写在字段上: min_length=6, max_length=128
            msg = "Password must contain 6 to 128 characters."
            raise ValidationError(msg)
        return make_password(value)


class ImagesFieldMixin:
    """图片地址的列表."""

    @staticmethod
    def get_images(obj: _HasImages) -> ImageList:
        """Images 字段 (一行一个地址) 转成 {"count", "data": [{"uri"}]}.

        Returns:
            图片的列表.

        """
        data = [Image(uri=item.strip()) for item in obj.images.split("\n") if item.strip()]
        return ImageList(count=len(data), data=data)


class TagsFieldMixin:
    """标签的列表."""

    @staticmethod
    def get_tags(obj: _HasTags) -> list[str]:
        """Tags 字段 (# 分隔) 转成列表.

        Returns:
            标签的列表.

        """
        return [item.strip() for item in obj.tags.split("#") if item.strip()]


class StartDateFieldMixin:
    """开始日期."""

    @staticmethod
    def get_start_date(obj: _HasStartTime) -> str:
        return localtime(obj.start_time).strftime("%Y-%m-%d")


class EndDateFieldMixin:
    """结束日期: 开始时间加上天数."""

    def get_end_date(self, obj: _HasPeriod) -> str:
        if obj.period <= 0:
            return ""
        return self.get_date_after_period(localtime(obj.start_time), obj.period)

    @staticmethod
    def get_date_after_period(date: dt.datetime, period: int) -> str:
        days = period
        if period >= 0:
            days = period - 1
        date_time = date + dt.timedelta(days=days)
        return date_time.strftime("%Y-%m-%d")
