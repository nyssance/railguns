import datetime

from django.apps.registry import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog
from rest_framework_simplejwt.views import token_obtain_pair, token_refresh

from .rest_framework.views import DownloadUrlView, UploadParamsView

# Django
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('jsi18n/',
         cache_page(86400,
                    key_prefix=f'js18n-{datetime.datetime.now().strftime("%Y%m%d")}')(JavaScriptCatalog.as_view()),
         name='javascript-catalog')
]
# Vendor
urlpatterns += [
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', token_obtain_pair, name='token_obtain_pair'),
    path('api/token/refresh/', token_refresh, name='token_refresh'),
    # path('search/', include('haystack.urls'))
]
# Railgun S
urlpatterns += [
    re_path(r'^download-url/(?P<cloud>(aliyun|aws))/$', DownloadUrlView.as_view(), name='download-url'),
    re_path(r'^upload-params/(?P<cloud>(aliyun|aws))/$', UploadParamsView.as_view(), name='upload-params'),
    path('favicon.ico', RedirectView.as_view(url=f'{settings.STATIC_URL}favicon.ico', permanent=True)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = _('app_name')
admin.site.site_title = _('app_name')
