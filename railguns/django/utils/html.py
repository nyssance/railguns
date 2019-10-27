from django.utils.html import format_html


# django 自带的 format_html_join 方法非常鸡肋
def format_html_field_join(field, format_string='{}', join_string='<br>'):
    return format_html(join_string.join(format_string.format(item) for item in field.all()))


def format_html_string_join(string, format_string='{}', join_string='<br>'):
    return format_html(join_string.join(format_string.format(item) for item in filter(None, string.split(','))))
