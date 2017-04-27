from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^downloads/$', views.downloads),
    url(r'^downloads/models\.zip', views.models_zip),
    url(r'^show_urls', views.show_urls)
]
