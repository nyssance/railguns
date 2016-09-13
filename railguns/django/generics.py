from django.conf import settings
from django.shortcuts import render


def list_view(request, name='', title=None, endpoint=''):
    title = title if title else name
    endpoint = endpoint if endpoint.strip() else '/{}{}'.format(settings.API_VERSION, request.get_full_path())
    templates = {'mobile': '{}/{}.html'.format('mobile', name)} if name else {'mobile': 'railguns/f7/list.html'}
    headers = get_headers(request, ['HTTP_APP_SCHEME', 'HTTP_USER_AGENT'])
    return render(request, templates['mobile'], locals())


def detail_view(request, *args, **kwargs):
    name = kwargs.get('name', '')
    title = kwargs.get('title', name)
    endpoint = kwargs.get('endpoint', '/{}{}'.format(settings.API_VERSION, request.get_full_path()))
    templates = {'mobile': '{}/{}.html'.format('mobile', name)} if name else {'mobile': 'railguns/f7/detail.html'}
    headers = get_headers(request, ['HTTP_APP_SCHEME', 'HTTP_USER_AGENT', 'HTTP_HOST'])
    print(headers)
    return render(request, templates['mobile'], locals())


def get_headers(request, keys=[]):
    return dict((key, value) for (key, value) in request.META.items() if key in keys)
