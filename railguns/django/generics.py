from typing import Optional
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import render
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic.base import TemplateView


def generate_link(urlstring: str, request: Optional[HttpRequest]) -> str:
    if not urlstring or urlparse(urlstring).scheme:  # 如果为空或有scheme
        return urlstring
    else:
        if request:
            app_scheme = request.headers.get('App-Scheme')
            if app_scheme:
                return f'{app_scheme}://{urlstring}'
        return f'/{urlstring}/' if urlstring != '/' else '/'


class WebView(TemplateView):
    name: Optional[str] = None
    title: Optional[str] = None
    endpoint: Optional[str] = ''

    def get(self, request, *args, **kwargs):
        if self.name.endswith('_create'):  # 创建页
            verbose_name = ' '.join(gettext(item) for item in self.name.split('_')[::-1])  # NY: 用gettext_lazy会报错
        else:
            verbose_name = _(self.name.replace('y_list', 'ies').replace('_list', 's').replace('_detail', ''))
        title = self.title if self.title is not None else verbose_name  # 用 is not None 才能传入空标题
        if self.endpoint is not None:
            version = settings.REST_FRAMEWORK.get('DEFAULT_VERSION', '')
            endpoint = self.endpoint or f'/api/{version}{request.get_full_path()}'
            dataset_endpoint = f' data-endpoint="{endpoint}"' if endpoint else ''
        template_name = self.template_name or f'web/{self.name}.html'
        extras = kwargs
        is_weixin = 'MicroMessenger' in request.headers['User-Agent']
        return render(request, template_name, locals())
