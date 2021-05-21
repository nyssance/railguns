import locale

from django.contrib import admin, messages
from django.core import serializers
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ...tools.utils import locale_currency
from ..db.models import OwnerModel


class PreviewMixin:
    image_width = 100
    image_height = 100

    @admin.display(description=_('preview'))
    def get_preview(self, obj):
        html = '<br>'.join('''<div style="width: {1}; height: {2}; overflow: hidden;">
                 <a href="{0}" rel="external" target="_blank">
                   <img src="{0}" max-width="{1}" max-height="{2} width="{1}" height="{2}">
                 </a>
               </div>'''.format(item.strip(), self.image_width, self.image_height) for item in obj.images.split('\n'))
        return format_html(html)


class CurrencyMixin:

    def format_currency(self, amount, min_value, currency='CNY'):
        value = amount / 100
        formatted = locale_currency(currency, value)
        if value < min_value:
            formatted = f'{formatted}<span style="color: red;"> (低于{locale.currency(min_value, False, True)})</span>'
        return format_html(formatted)


class SuperAdmin(CurrencyMixin, PreviewMixin, admin.ModelAdmin):
    readonly_fields = []  # 默认从tuple改为list

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in obj._meta.get_fields() if not f.editable] + self.readonly_fields
        return super().get_readonly_fields(request)

    def get_sortable_by(self, request):
        if self.readonly_fields and isinstance(self.readonly_fields, tuple):
            messages.warning(request, 'readonly_fields 为 tuple, 建议改为 list, 修改页面未容错，会报错')
        return super().get_sortable_by(request)

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # 如果obj.pk不存在, 为新创建
            if isinstance(obj, OwnerModel):
                obj.username = request.user.username
                obj.user_avatar = request.user.avatar
        super().save_model(request, obj, form, change)

    def log_change(self, request, obj, message):
        new_message = f'json: {serializers.serialize("json", [obj])}'
        super().log_change(request, obj, new_message)
