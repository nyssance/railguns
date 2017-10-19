from collections import OrderedDict


def get_list(data):
    return OrderedDict([('count', len(data)), ('next', None), ('previous', None), ('results', data)])
