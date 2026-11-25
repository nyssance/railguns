import operator
import re
from contextlib import ExitStack
from enum import Enum
from inspect import Parameter, signature
from typing import Literal, get_args, get_origin
lazy from collections.abc import Callable, Collection, Mapping

from freeman.testing import TestClient
lazy from freeman.api import BoltAPI

from railguns.rest_framework import _bolt, auth

WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")
LOGOUT = (auth.logout, auth.logout_all)


def sample_value(annotation: object) -> str:
    """路径参数的一个合法值: 只能取某几个值的 (Literal, Enum) 取第一个, 其余是 1.

    Returns:
        参数的值.

    """
    if get_origin(annotation) is Literal:
        return str(get_args(annotation)[0])
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return str(next(iter(annotation)).value)
    return "1"


def sample_path(path: str, handler: Callable | None = None) -> str:
    """把路由模板变成一个具体地址: /orders/{pk}/items/{name:path} -> /orders/1/items/sample.

    给了处理函数时, 参数的值按它的类型取, 比如 /exams/{category} 的 category 只能是几个值之一, 就取第一个.

    Returns:
        具体的地址.

    """
    path = re.sub(r"\{[^}:]+:path\}", "sample", path)
    parameters: Mapping[str, Parameter] = signature(handler, eval_str=True).parameters if handler is not None else {}

    def value(match: re.Match[str]) -> str:
        found = parameters.get(match.group(1))
        return sample_value(found.annotation) if found is not None else "1"

    return re.sub(r"\{(\w+)[^}]*\}", value, path)


def access_matrix(
    api: BoltAPI, actors: dict, *, methods: Collection[str] | None = None, client: TestClient | None = None
) -> dict:
    """每条路由用每种身份请求一次, 返回 {"GET /api/v1/orders/1": {"anonymous": 401, "staff": 200}}.

    actors: {身份名: 请求头}, 比如 {"anonymous": {}, "staff": {"Authorization": "Bearer ..."}}
    methods: 只测这些请求方法, 默认全部. 写方法发的是空的 JSON 对象, 用来确认权限判断发生在参数校验之前.
    client: 已经打开的 Bolt TestClient. 不传时自己开一个, 处理函数的异常记为 500.

    登出的两个接口不在矩阵里: 请求它们会让这个身份的令牌失效, 之后的每一格都会变成 401.

    Returns:
        {"方法 地址": {身份名: 状态码}}.

    """
    with ExitStack() as stack:
        opened = client if client is not None else stack.enter_context(TestClient(api, raise_server_exceptions=False))
        matrix = {}
        routes = {(method, path): handler for method, path, handler in _bolt.routes(api) if handler not in LOGOUT}
        for (method, path), handler in sorted(routes.items(), key=operator.itemgetter(0)):
            if methods and method not in methods:
                continue
            url = sample_path(path, handler)
            body = {} if method in WRITE_METHODS else None
            matrix[f"{method} {url}"] = {
                name: opened.request(method, url, headers=headers, json=body).status_code
                for name, headers in actors.items()
            }
        return matrix
