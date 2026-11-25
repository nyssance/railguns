import locale
lazy from collections.abc import Callable

from django.contrib import admin, messages
from django.core import serializers
from django.utils.html import format_html, format_html_join
from django.utils.safestring import SafeText, mark_safe
from django.utils.translation import gettext_lazy as _
lazy from django.contrib.admin.models import LogEntry
lazy from django.db.models import Model
lazy from django.forms import ModelForm
lazy from django.http import HttpRequest

from railguns.django.db._introspect import options
from railguns.django.db.models import OwnerModel
from railguns.tools.utils import locale_currency

type _Display = str | Callable[[Model], str | bool]  # 后台列表的一列: 字段名或者函数


class PreviewMixin:
    """后台列表的图片预览: obj.images 每行一个图片地址."""

    image_width = 100
    image_height = 100

    @admin.display(description=_("preview"))
    def get_preview(self, obj: Model) -> SafeText:
        return format_html_join(
            mark_safe("<br>"),
            """<div style="width: {1}; height: {2}; overflow: hidden;">
                 <a href="{0}" rel="external" target="_blank">
                   <img src="{0}" max-width="{1}" max-height="{2}" width="{1}" height="{2}">
                 </a>
               </div>""",
            ((item.strip(), self.image_width, self.image_height) for item in obj.images.split("\n") if item.strip()),
        )


class CurrencyMixin:
    """后台的金额显示: 金额以分为单位."""

    def format_currency(self, amount: int, min_value: int, currency: str = "CNY") -> SafeText:
        value = amount / 100
        formatted = locale_currency(currency, value)
        if value < min_value:
            return format_html(
                '{}<span style="color: red;"> (低于{})</span>',
                formatted,
                locale.currency(min_value, symbol=False, grouping=True),
            )
        return format_html("{}", formatted)


class SuperAdmin(CurrencyMixin, PreviewMixin, admin.ModelAdmin):
    """后台的基类: 不可编辑的字段只读, 记录修改时存一份 JSON."""

    readonly_fields = []

    def get_readonly_fields(self, request: HttpRequest, obj: Model | None = None) -> list[str] | tuple[str, ...]:
        if obj:
            return [*(f.name for f in options(obj).get_fields() if not f.editable), *self.readonly_fields]
        return super().get_readonly_fields(request)

    def get_sortable_by(self, request: HttpRequest) -> list[_Display] | tuple[_Display, ...]:
        if self.readonly_fields and isinstance(self.readonly_fields, tuple):
            messages.warning(request, "readonly_fields 为 tuple, 建议改为 list, 修改页面未容错, 会报错")
        return super().get_sortable_by(request)

    def save_model(self, request: HttpRequest, obj: Model, form: ModelForm, change: bool) -> None:
        if not obj.pk and isinstance(obj, OwnerModel):  # 如果obj.pk不存在, 为新创建
            obj.username = request.user.username
            obj.user_avatar = request.user.avatar
        super().save_model(request, obj, form, change)

    def log_change(self, request: HttpRequest, obj: Model, message: object) -> LogEntry:
        new_message = f"json: {serializers.serialize("json", [obj])}"
        return super().log_change(request, obj, new_message)
