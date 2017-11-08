from django.utils.html import format_html


# django 自带的 format_html_join 方法非常鸡肋
def format_html_field_join(field, format_string='{}'):
    return format_html('<br>'.join(format_string.format(item) for item in field.all()))


def format_html_string_join(string):
    return format_html('<br>'.join(string.split()))
