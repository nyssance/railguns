from collections import OrderedDict


def get_nested_list[T](data: list[T]) -> OrderedDict[str, int | list[T]]:
    """把列表包成 {count, data}.

    Returns:
        带数量的列表.

    """
    return OrderedDict([("count", len(data)), ("data", data)])
