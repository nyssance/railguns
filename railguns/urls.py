from django.apps.registry import apps
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView, TemplateView
from django.views.i18n import javascript_catalog
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token

from .rest_framework.views import download_url, upload_params
from .views import SwaggerSchemaView


# 系统自带:
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/(?P<packages>\S+?)/$', javascript_catalog)
]
# 第三方:
urlpatterns += [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^api-token-refresh/', refresh_jwt_token),
    url(r'^api-token-verify/', verify_jwt_token),
    url(r'^developer/documentation/', SwaggerSchemaView.as_view()),
    # url(r'^search/', include('haystack.urls'))
]
# RailgunS:
urlpatterns += [
    url(r'^download_url/(?P<pk>\w+)/$', download_url, name='download_url'),
    url(r'^upload_params/(?P<pk>\w+)/$', upload_params, name='upload_params'),
    url(r'^favicon\.ico', RedirectView.as_view(url='{}favicon.ico'.format(settings.STATIC_URL), permanent=True)),
    url(r'^robots\.txt', cache_page(60 * 60)(TemplateView.as_view(template_name='{}'.format('robots_test.txt' if settings.TEST_ENV else 'robots.txt'), content_type='text/plain')))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if apps.is_installed('rosetta'):
    urlpatterns += [url(r'^rosetta/', include('rosetta.urls'))]
