from django.urls import path

from . import views


urlpatterns = [
    url('', views.index, name='index'),
    url('downloads/', views.downloads),
    url('downloads/models\.zip', views.models_zip),
    url('show_urls', views.show_urls)
]
