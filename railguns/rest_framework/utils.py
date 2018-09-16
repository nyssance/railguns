from collections import OrderedDict


def get_nested_list(data):
    return OrderedDict([('count', len(data)), ('data', data)])
