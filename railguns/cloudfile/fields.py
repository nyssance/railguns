from django.db.models import Field

from .widgets import CloudFileWidget


class CloudFileField(Field):

    def __init__(self, *args, **kwargs):
        dest = kwargs.pop('dest', None)
        self.widget = CloudFileWidget(dest=dest)
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'TextField'

    def formfield(self, *args, **kwargs):
        kwargs['widget'] = self.widget
        return super().formfield(*args, **kwargs)
