from rest_framework.pagination import PageNumberPagination
from rest_framework.settings import api_settings


class StandardResultsSetPagination(PageNumberPagination):
    page_size = api_settings.PAGE_SIZE if api_settings.PAGE_SIZE else 20
    page_size_query_param = 'page_size'
    max_page_size = 1000
