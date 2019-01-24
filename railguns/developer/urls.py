from django.contrib.auth.decorators import login_required
from django.urls import path, re_path
from django.views.decorators.cache import cache_page
from railguns.django.generics import WebView

from . import views

app_name = 'developer'
urlpatterns = [
    path(
        '',
        cache_page(0)(login_required(
            WebView.as_view(name='index', endpoint='', template_name='railguns/developer/developer_index.html'))),
        name='index'),
    path(
        'downloads/',
        cache_page(300)(login_required(
            WebView.as_view(name='index', endpoint='', template_name='railguns/developer/downloads.html'))),
        name='downloads'),
    re_path(r'^downloads/(?P<language>(kt|swift)).zip$', login_required(views.zip_view))
]
