from typing import Optional
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import render
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic.base import TemplateView


def get_headers(request, keys):
    return dict((key, value) for (key, value) in request.META.items() if key in keys)


def generate_link(urlstring: str, request: Optional[HttpRequest]) -> str:
    """注意前端传入格式应为 App-Scheme 首字母大写加中划线这样"""
    if not urlstring or urlparse(urlstring).scheme:  # 如果为空或有scheme
        return urlstring
    else:
        if request:
            headers = get_headers(request, ['HTTP_APP_SCHEME', 'HTTP_USER_AGENT', 'HTTP_HOST'])
            # print(headers)
            app_scheme = headers.get('HTTP_APP_SCHEME')
            if app_scheme:
                return f'{app_scheme}://{urlstring}'
        return f'/{urlstring}/' if urlstring != "/" else "/"


class WebView(TemplateView):
    name: Optional[str] = None
    title: Optional[str] = None
    endpoint: Optional[str] = None

    def get(self, request, *args, **kwargs):
        if self.name.endswith('_create'):  # 创建页
            verbose_name = ' '.join(gettext(item) for item in self.name.split('_')[::-1])  # NY: 用gettext_lazy会报错
        else:
            verbose_name = _(self.name.replace('y_list', 'ies').replace('_list', 's').replace('_detail', ''))
        title = self.title if self.title is not None else verbose_name  # 用 is not None 才能传入空标题
        endpoint = self.endpoint if self.endpoint is not None else f'/api/{settings.REST_FRAMEWORK["DEFAULT_VERSION"]}{request.get_full_path()}'
        template_name = self.template_name if self.template_name else f'web/{self.name}.html'
        extras = kwargs
        is_weixin = 'MicroMessenger' in request.META['HTTP_USER_AGENT']
        return render(request, template_name, locals())
