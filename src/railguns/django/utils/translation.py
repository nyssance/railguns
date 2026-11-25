from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
lazy from django.utils.functional import Promise


def dj_gettext(message: str) -> Promise:
    """获取Django原生翻译.

    Returns:
        延迟翻译的字符串.

    """
    return _(message)


def format_gettext_lazy(message1: str, message2: str) -> Promise:
    """两个词分别翻译, 用空格连起来.

    Returns:
        延迟格式化的字符串.

    """
    return format_lazy("{} {}", _(message1), _(message2))


def get_untranslated_text(text: Promise) -> object:
    """延迟翻译的字符串的原文.

    Returns:
        原文, 取不到时是 text 本身.

    """
    # SO https://stackoverflow.com/questions/5143822/access-untranslated-content-of-djangos-ugettext-lazy
    # with translation.override("en"):
    #     return force_text(text)
    untranslated_text = text
    try:
        # 虽然不建议使用, 但是不用的话得到的是英语翻译的(首字母会大写)
        untranslated_text = text._args[0]
    except Exception as e:
        print(f"Exception: {text} {e}")
    return untranslated_text
