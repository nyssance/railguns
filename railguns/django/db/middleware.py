import threading


request_cfg = threading.local()


class MultiDBRouterMiddleware(object):
    """
    https://docs.djangoproject.com/en/dev/topics/http/middleware/#process-view
    https://github.com/transientskp/banana/blob/master/project/multidb.py
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        request_cfg.pk = view_kwargs.get('pk')

    def process_response(self, request, response):
        if hasattr(request_cfg, 'pk'):
            del request_cfg.pk
        return response
