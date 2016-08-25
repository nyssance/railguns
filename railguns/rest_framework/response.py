from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST


class ResponseBadRequest(Response):
    def __init__(self, detail=''):
        return super(ResponseBadRequest, self).__init__({'detail': detail}, status=HTTP_400_BAD_REQUEST)
