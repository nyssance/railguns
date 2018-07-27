from django.apps.registry import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.utils.translation import gettext, gettext_lazy as _
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.documentation import include_docs_urls
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token

from .rest_framework.views import DownloadUrlView, UploadParamsView

# Django
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    # https://docs.djangoproject.com/en/dev/topics/i18n/translation/#note-on-performance
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog')
]
# Vendor
urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
    path('api-token-auth/', obtain_jwt_token),
    path('api-token-refresh/', refresh_jwt_token),
    path('api-token-verify/', verify_jwt_token),
    # path('search/', include('haystack.urls'))
]
# Docs
API_TITLE = '{} API'.format(gettext('app_name'))
API_DESCRIPTION = '...'

schema_view = get_schema_view(
    openapi.Info(title=API_TITLE, default_version='v1', description=API_DESCRIPTION),
    validators=['flex', 'ssv'],
    permission_classes=[permissions.IsAdminUser])

urlpatterns += [
    path('docs/',
         include_docs_urls(title=API_TITLE, description=API_DESCRIPTION, permission_classes=[permissions.IsAdminUser])),
    re_path(r'swagger(?P<format>.json|.yaml)', schema_view.without_ui(), name='schema-json'),
    path('swagger/', schema_view.with_ui(), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc'), name='schema-redoc')
]
# Railgun S
urlpatterns += [
    re_path(r'download_url/(?P<cloud>(aliyun|oss))/$', DownloadUrlView.as_view(), name='download-url'),
    re_path(r'upload_params/(?P<cloud>(aliyun|oss|aws|s3))/$', UploadParamsView.as_view(), name='upload-params'),
    path('favicon.ico', RedirectView.as_view(url='{}favicon.ico'.format(settings.STATIC_URL), permanent=True))
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if apps.is_installed('rosetta'):
    urlpatterns += [path('rosetta/', include('rosetta.urls'))]

admin.site.site_header = _('app_name')
admin.site.site_title = _('app_name')
