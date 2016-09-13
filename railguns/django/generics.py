from django.conf import settings
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView


# headers = get_headers(request, ['HTTP_APP_SCHEME', 'HTTP_USER_AGENT', 'HTTP_HOST'])
# print(headers)
def get_headers(request, keys=[]):
    return dict((key, value) for (key, value) in request.META.items() if key in keys)


class BaseView(TemplateView):
    name = None


class WebView(BaseView):
    def get(self, request, *args, **kwargs):
        title = kwargs.get('title', '{} - {}'.format(_(self.name), _('app_name')))
        endpoint = kwargs.get('endpoint', '/{}{}'.format(settings.API_VERSION, request.get_full_path()))
        template_name = self.template_name if self.template_name else '{}.html'.format(self.name)
        return render(request, template_name, locals())


class MobileView(BaseView):
    def get(self, request, *args, **kwargs):
        title = kwargs.get('title', _(self.name))
        endpoint = kwargs.get('endpoint', '/{}{}'.format(settings.API_VERSION, request.get_full_path().replace(kwargs.get('path', '/m/'), '/')))
        template_name = self.template_name if self.template_name else 'mobile/{}.html'.format(self.name)
        return render(request, template_name, locals())
