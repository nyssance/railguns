from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('downloads/', views.downloads),
    path('downloads/models\.zip', views.models_zip),
    path('show_urls', views.show_urls)
]
