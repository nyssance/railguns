from os.path import abspath, dirname
from urllib.parse import urlparse

from django.conf import settings


def get_name(file):
    return '.'.join(dirname(abspath(file)).replace(dirname(settings.PROJECT_PATH), '').split('/')[1:])


def get_header(request, key):
    return dict(('header', value) for (header, value) in request.META.items() if header == key).get('header')


def get_uri(urlstring, request):
    if urlstring == '' or urlparse(urlstring).scheme:  # 如果为空或有scheme
        return urlstring
    else:
        app_scheme = get_header(request, 'HTTP_APP_SCHEME')
        if app_scheme:
            return '{}:/{}'.format(app_scheme, urlstring)
        else:
            return '{}{}/'.format(settings.BASE_URL, urlstring)
