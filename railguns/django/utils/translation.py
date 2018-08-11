from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _


def dj_gettext(message):
    """获取Django原生翻译"""
    return _(message)


def format_gettext_lazy(message1, message2):
    return format_lazy('{} {}', _(message1), _(message2))
