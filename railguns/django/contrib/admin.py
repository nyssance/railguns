import locale

from django.contrib import admin
from django.core import serializers
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..db.models import OwnerModel


class PreviewMixin(object):
    image_width = 200
    image_height = 100

    def get_preview(self, obj):
        html = '<br>'.join('<a href="{0}" rel="external" target="_blank"><img src="{0}" width="{1}" height="{2}"></a>'.format(
            item.strip(), self.image_width, self.image_height) for item in obj.images.split('\n'))
        return format_html(html)
    get_preview.short_description = _('preview')


class CurrencyMixin(object):

    def format_currency(self, amount, min):
        value = amount / 100
        locale.setlocale(locale.LC_ALL, '')
        locale._override_localeconv = {'n_sign_posn': 1}
        formatted = locale.currency(value, grouping=True)
        if value < min:
            formatted = '{}<span style="color: red;"> (低于{})</span>'.format(formatted, locale.currency(min, False, True))
        return format_html(formatted)


class SuperAdmin(CurrencyMixin, PreviewMixin, admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # 如果obj.pk不存在, 为新创建
            if 'user_id' in [f.name for f in obj._meta.get_fields()]:
                if not obj.user_id:
                    obj.user_id = request.user.id
            if isinstance(obj, OwnerModel):
                obj.username = request.user.username
                obj.user_avatar = request.user.avatar
        super().save_model(request, obj, form, change)

    def log_change(self, request, obj, message):
        new_message = '{}'.format(serializers.serialize('json', [obj]))
        super().log_change(request, obj, new_message)
