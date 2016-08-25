"""
https://github.com/tomchristie/django-rest-framework/issues/944
"""
import re


first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def camelcase_to_underscore(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def underscore_to_camelcase(name, lower_first=True):
    result = ''.join(char.capitalize() for char in name.split('_'))
    if lower_first:
        return result[0].lower() + result[1:]
    else:
        return result


def recursive_key_map(function, data):
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if isinstance(key, str):
                new_key = function(key)
            new_dict[new_key] = recursive_key_map(function, value)
        return new_dict
    elif isinstance(data, (list, tuple)):
        return [recursive_key_map(function, value) for value in data]
    else:
        return data
