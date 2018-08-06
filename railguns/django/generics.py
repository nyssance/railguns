from urllib.parse import urlparse

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic.base import TemplateView


def get_headers(request, keys=[]):
    return dict((key, value) for (key, value) in request.META.items() if key in keys)


def generate_uri(urlstring, request):
    if not urlstring or urlparse(urlstring).scheme:  # 如果为空或有scheme
        return urlstring
    else:
        # headers = get_headers(request, ['HTTP_APP_SCHEME', 'HTTP_USER_AGENT', 'HTTP_HOST'])
        # print(headers)
        app_scheme = get_headers(request, ['HTTP_APP_SCHEME']).get('HTTP_APP_SCHEME')
        if app_scheme:
            return '{}:/{}'.format(app_scheme, urlstring)
        else:
            return '{}/'.format(urlstring)


def get_title(string):
    return '{}{}'.format('🦄 ' if settings.DEBUG else '', string)


class WebView(TemplateView):
    name = None
    title = None
    endpoint = None

    def get(self, request, *args, **kwargs):
        if self.name.endswith('_create'):  # 创建页
            verbose_name = (' ').join(gettext(item) for item in self.name.split('_')[::-1])  # NY: 用gettext_lazy会报错
        else:
            verbose_name = _(self.name.replace('y_list', 'ies').replace('_list', 's').replace('_detail', ''))
        title = get_title(self.title if self.title is not None else verbose_name)  # 用 is not None 才能传入空标题
        endpoint = self.endpoint if self.endpoint is not None else '/api/{}{}'.format(
            settings.REST_FRAMEWORK['DEFAULT_VERSION'], request.get_full_path())
        template_name = self.template_name if self.template_name else 'web/{}.html'.format(self.name)
        extras = kwargs
        is_weixin = 'MicroMessenger' in request.META.get('HTTP_USER_AGENT')
        return render(request, template_name, locals())
