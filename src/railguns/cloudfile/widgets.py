from typing import Any, ClassVar, override
from urllib.parse import unquote_plus

from django.conf import settings
from django.forms import widgets
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import SafeString, mark_safe
lazy from django.forms.renderers import BaseRenderer


class CloudFileWidget(widgets.TextInput):
    """直传对象存储的文件输入框."""

    class Media:
        """上传组件的脚本和样式."""

        js: ClassVar[list[str]] = ["s3direct/dist/index.js"]
        css: ClassVar[dict[str, list[str]]] = {"all": ["s3direct/dist/index.css"]}

    def __init__(self, *args: Any, dest: str | None = None, **kwargs: Any) -> None:
        """参数: dest 是上传的目标, 其余参数和 TextInput 一样."""
        self.dest = dest
        super().__init__(*args, **kwargs)

    @override
    def render(
        self, name: str, value: str | None, attrs: dict | None = None, renderer: BaseRenderer | None = None
    ) -> SafeString:
        file_url = value or ""
        csrf_cookie_name = getattr(settings, "CSRF_COOKIE_NAME", "csrftoken")
        ctx = {
            "policy_url": f"/api/{settings.API_VERSION}/upload-params/aliyun",
            "signing_url": reverse("s3direct-signing"),
            "dest": self.dest,
            "name": name,
            "csrf_cookie_name": csrf_cookie_name,
            "file_url": file_url,
            "file_name": unquote_plus(file_url).rpartition("/")[2],  # 和 os.path.basename 一样取最后一段
        }
        return mark_safe(render_to_string("s3direct/s3direct-widget.tpl", ctx))
