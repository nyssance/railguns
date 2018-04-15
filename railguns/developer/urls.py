from django.urls import path

from . import views

app_name = 'developer'
urlpatterns = [
    path('', views.index, name='index'),
    path('downloads/', views.downloads, name='downloads'),
    path('downloads/models.zip', views.ModelZipView.as_view(), {
        'file_path': 'apps/api/serializers.py',
        'filter_list': ['id_str']
    }),
    path('show_urls', views.show_urls)
]
