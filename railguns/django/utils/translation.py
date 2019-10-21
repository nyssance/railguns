from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _


def dj_gettext(message):
    """获取Django原生翻译"""
    return _(message)


def format_gettext_lazy(message1, message2):
    return format_lazy('{} {}', _(message1), _(message2))


def get_untranslated_text(text):
    # SO https://stackoverflow.com/questions/5143822/access-untranslated-content-of-djangos-ugettext-lazy
    # with translation.override('en'):
    #     return force_text(text)
    untranslated_text = text
    try:
        untranslated_text = text._proxy____args[0]  # 虽然不建议使用, 但是不用的话得到的是英语翻译的(首字母会大写)
    except Exception as e:
        print(f'Exception: {text} {e}')
    return untranslated_text
