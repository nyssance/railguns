from typing import Any, override

from django.db.models import Field
lazy from django import forms

from .widgets import CloudFileWidget


class CloudFileField(Field):
    """对象存储里的文件地址, 数据库里是文本, 表单里用 CloudFileWidget."""

    def __init__(self, *args: Any, dest: str | None = None, **kwargs: Any) -> None:
        """参数: dest 是上传的目标, 其余参数和 Field 一样."""
        self.widget = CloudFileWidget(dest=dest)
        super().__init__(*args, **kwargs)

    @override
    def get_internal_type(self) -> str:
        return "TextField"

    @override
    def formfield(self, *args: Any, **kwargs: Any) -> forms.Field | None:
        kwargs["widget"] = self.widget
        return super().formfield(*args, **kwargs)
