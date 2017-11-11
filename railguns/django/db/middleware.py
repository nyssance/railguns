import threading


request_cfg = threading.local()


class MultiDBRouterMiddleware(object):
    """
    https://docs.djangoproject.com/en/dev/topics/http/middleware/#process-view
    https://github.com/transientskp/banana/blob/master/project/multidb.py
    https://github.com/yandex/django_replicated/blob/3aeb5df9b7829105201e00a9a177ba6e51c1699c/django_replicated/middleware.py
    https://github.com/jbalogh/django-multidb-router/blob/master/multidb/middleware.py
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        request_cfg.pk = view_kwargs.get('pk')

    def __call__(self, request):
        response = self.get_response(request)
        if hasattr(request_cfg, 'pk'):
            del request_cfg.pk
        return response
