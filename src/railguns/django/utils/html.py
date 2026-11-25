from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
lazy from django.db.models import Manager
lazy from django.utils.safestring import SafeString


# django 自带的 format_html_join 方法非常鸡肋
def format_html_field_join(
    field: Manager, format_string: str = "{}", join_string: str = mark_safe("<br>")
) -> SafeString:
    return format_html_join(join_string, format_string, ((item,) for item in field.all()))


def format_html_string_join(string: str, format_string: str = "{}", join_string: str = mark_safe("<br>")) -> SafeString:
    return format_html_join(join_string, format_string, ((item,) for item in filter(None, string.split(","))))
