import datetime as dt

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog

from .rest_framework import auth, views
from .rest_framework.api import API

# Django
urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path(
        "jsi18n/",
        cache_page(86400, key_prefix=f"js18n-{dt.datetime.now().astimezone().strftime("%Y%m%d")}")(
            JavaScriptCatalog.as_view()
        ),
        name="javascript-catalog",
    ),
]
# Vendor
urlpatterns += [
    path("ckeditor5/", include("django_ckeditor_5.urls"))
    # path("search/", include("haystack.urls"))
]
# Railgun S
urlpatterns += [path("favicon.ico", RedirectView.as_view(url=f"{settings.STATIC_URL}favicon.ico", permanent=True))]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API, 项目入口里挂载一次: api.mount("/api/v1", railguns.urls.api)
api = API()
api.post("/auth/login")(auth.login_handler())
api.post("/auth/refresh")(auth.refresh)
api.post("/auth/logout", auth=[auth.access_auth], guards=[auth.IsAuthenticated()])(auth.logout)
api.post("/auth/logout-all", auth=[auth.access_auth], guards=[auth.IsAuthenticated()])(auth.logout_all)
api.get("/download-url/{cloud}", **views.STORAGE)(views.download_url)
api.post("/upload-params/{cloud}", **views.STORAGE)(views.upload_params)

admin.site.site_header = _("app_name")
admin.site.site_title = _("app_name")
