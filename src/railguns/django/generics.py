from typing import cast
from urllib.parse import urlparse

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
lazy from django.http import HttpRequest, HttpResponse


def generate_link(urlstring: str, request: HttpRequest | None) -> str:
    if not urlstring or urlparse(urlstring).scheme:  # 如果为空或有scheme
        return urlstring
    if request:
        app_scheme = request.headers.get("App-Scheme")
        if app_scheme:
            return f"{app_scheme}://{urlstring}"
    return f"/{urlstring}/" if urlstring != "/" else "/"


class WebView(TemplateView):
    """网页: 模板默认是 web/{name}.html, 页面通过 data-endpoint 调接口."""

    name: str | None = None
    title: str | None = None
    endpoint: str | None = ""

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        name = cast("str", self.name)  # 子类必须设置 name
        if name.endswith("_create"):  # 创建页
            verbose_name = " ".join(gettext(item) for item in name.split("_")[::-1])  # NY: 用gettext_lazy会报错
        else:
            verbose_name = _(name.replace("y_list", "ies").replace("_list", "s").replace("_detail", ""))
        title = self.title if self.title is not None else verbose_name  # 用 is not None 才能传入空标题
        context: dict[str, object] = {"self": self, "request": request, "args": args, "kwargs": kwargs}
        context |= {"verbose_name": verbose_name, "title": title}
        if self.endpoint is not None:
            version = getattr(settings, "API_VERSION", "")
            endpoint = self.endpoint or f"/api/{version}{request.get_full_path()}"
            dataset_endpoint = f' data-endpoint="{endpoint}"' if endpoint else ""
            context |= {"version": version, "endpoint": endpoint, "dataset_endpoint": dataset_endpoint}
        template_name = self.template_name or f"web/{name}.html"
        is_weixin = "MicroMessenger" in request.headers.get("User-Agent", "")
        context |= {"template_name": template_name, "extras": kwargs, "is_weixin": is_weixin}
        return render(request, template_name, context)
