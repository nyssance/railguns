from urllib.parse import urlparse

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView


def get_headers(request, keys=[]):
    return dict((key, value) for (key, value) in request.META.items() if key in keys)


def generate_uri(urlstring, request):
    if urlstring == '' or urlparse(urlstring).scheme:  # 如果为空或有scheme
        return urlstring
    else:
        # headers = get_headers(request, ['HTTP_APP_SCHEME', 'HTTP_USER_AGENT', 'HTTP_HOST'])
        # print(headers)
        app_scheme = get_headers(request, ['HTTP_APP_SCHEME']).get('HTTP_APP_SCHEME')
        if app_scheme:
            return '{}:/{}'.format(app_scheme, urlstring)
        else:
            return '{}{}/'.format(settings.BASE_URL, urlstring)


class BaseView(TemplateView):
    name = None


class WebView(TemplateView):
    name = None

    def get(self, request, *args, **kwargs):
        verbose_name = _(self.name.replace('_list', 's').replace('_detail', ''))
        title = kwargs.get('title', verbose_name)
        # title = kwargs.get('title', '{} - {}'.format(verbose_name, _('app_name'))) // TODO: PC版用这个
        endpoint = kwargs.get('endpoint', '/{}{}'.format(settings.API_VERSION, request.get_full_path()))
        template_name = self.template_name if self.template_name else '{}.html'.format(self.name)
        return render(request, template_name, locals())
