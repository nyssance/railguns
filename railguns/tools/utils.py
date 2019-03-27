import locale


def locale_currency(currency, amount):
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8' if currency == 'CNY' else '')
    locale._override_localeconv = {'n_sign_posn': 1}
    return locale.currency(amount, grouping=True)
