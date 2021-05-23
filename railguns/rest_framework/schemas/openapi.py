from django.conf import settings
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.schemas.utils import is_list_view


class AutoSchema(AutoSchema):

    def get_operation_id(self, path, method):
        method_name = getattr(self.view, 'action', method.lower())
        if is_list_view(path, method, self.view):
            action = 'list'
        elif method_name not in self.method_mapping:
            action = self._to_camel_case(method_name)
        else:
            action = self.method_mapping[method.lower()]
        name = self.get_operation_id_base(path, method, action)
        return name + action.capitalize()

    def get_tags(self, path, method):
        if self._tags:
            return self._tags
        if path.startswith('/'):
            path = path[1:]
        version = settings.REST_FRAMEWORK.get('DEFAULT_VERSION', '')
        return [path.split('api/')[1].split(f'{version}/')[1].split('/')[0]]
