def underscore_to_camelcase(name, lower_first=True):
    result = name.title().replace('_', '')
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
