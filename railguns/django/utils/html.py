from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe


def format_field_join(field):
    return format_html_join(mark_safe('<br>'), '{}', (item.__str__() for item in field.all()))


def format_string_join(string):
    return format_html(mark_safe('<br>').join(string.split()))
