import locale
lazy from decimal import Decimal


def locale_currency(currency: str, amount: float | Decimal) -> str:
    """按货币的本地格式显示金额, 负号在前.

    Returns:
        格式化后的金额.

    """
    locale.setlocale(locale.LC_ALL, "zh_CN.UTF-8" if currency == "CNY" else "")
    locale._override_localeconv = {"n_sign_posn": 1}
    return locale.currency(amount, grouping=True)
