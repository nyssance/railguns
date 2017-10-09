import threading


request_cfg = threading.local()


class MultiDBRouterMiddleware(object):  # TODO: 待测试1.10上对不对，此版本只能用于1.10及以上
    """
    https://docs.djangoproject.com/en/dev/topics/http/middleware/#process-view
    https://github.com/transientskp/banana/blob/master/project/multidb.py
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
