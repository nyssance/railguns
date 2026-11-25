"""接口定义: 引擎生成的 OpenAPI 加上 railguns 的约定 (接口名, 分页和筛选参数), 并检查客户端生成器的限制."""

import re
from inspect import signature
from typing import Any
lazy from collections.abc import Callable

from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models import IntegerField, Model
from freeman.openapi.schema_generator import SchemaGenerator
from inflection import pluralize
lazy from django_filters.filters import Filter
lazy from freeman import BoltAPI
lazy from freeman.openapi import OpenAPIConfig

from railguns.django.db._introspect import options
from railguns.rest_framework import _bolt, idempotency
from railguns.rest_framework.pagination import MAX_PAGE_SIZE, PAGE_SIZE, Page

FILTER_TYPES = {
    "BooleanFilter": {"type": "boolean"},
    "DateFilter": {"type": "string", "format": "date"},
    "DateTimeFilter": {"type": "string", "format": "date-time"},
    "NumberFilter": {"type": "number"},
    "UUIDFilter": {"type": "string", "format": "uuid"},
}


# 每个列表接口都有的分页参数
PAGE_PARAMETERS = [
    {
        "name": "page",
        "in": "query",
        "required": False,
        "description": "页码, 从 1 开始",
        "schema": {"type": "integer", "minimum": 1, "default": 1},
    },
    {
        "name": "page_size",
        "in": "query",
        "required": False,
        "description": "每页条数",
        "schema": {"type": "integer", "minimum": 1, "maximum": MAX_PAGE_SIZE, "default": PAGE_SIZE},
    },
]


class AutoSchema:
    """生成项目的接口定义."""

    def __init__(self, api: BoltAPI, config: OpenAPIConfig) -> None:
        """参数: 项目的接口入口和引擎的接口定义配置."""
        self.api = api
        self.config = config

    def generate(self) -> dict[str, Any]:
        """生成接口定义并检查.

        Returns:
            OpenAPI 文档.

        """
        schema = SchemaGenerator(self.api, self.config).generate().to_schema()
        for method, path, handler in _bolt.routes(self.api):
            view = getattr(handler, "railguns_view", None)
            operation = schema["paths"].get(path, {}).get(method.lower())
            if not operation:
                continue
            if getattr(handler, "railguns_idempotent", False):
                operation.setdefault("parameters", []).append(dict(idempotency.PARAMETER))
            if not view:  # 业务接口: 函数名转成同样的写法, upload_params -> UploadParams
                operation["operationId"] = "".join(part.capitalize() for part in handler.__name__.split("_"))
                self.check_response_type(operation, f"{method} {path}")
                self.add_page_parameters(operation, handler)
                continue
            action = handler.railguns_action
            model = view.get_model()
            # 接口名取自视图类名, 类名在项目里是唯一的:
            # ArticleList + list -> ArticlesList, ArticleDetail + retrieve -> ArticleRetrieve
            name = re.sub(r"(List|Detail|Create|ViewSet|API)$", "", view.__name__) or view.__name__
            if action == "list":
                name = pluralize(name)
            operation["operationId"] = name + {"partial_update": "PartialUpdate"}.get(action, action.capitalize())
            if not operation.get("tags"):
                operation["tags"] = [path.rstrip("/").split("/")[-2 if "{" in path else -1]]
            if action != "list":
                continue
            parameters = operation.setdefault("parameters", [])
            parameters.extend(PAGE_PARAMETERS)
            filters = view.get_filterset_class()
            if filters:
                parameters = operation.setdefault("parameters", [])
                existing = {p.get("name") for p in parameters if p.get("in") == "query"}
                parameters.extend(
                    {
                        "name": name,
                        "in": "query",
                        "required": bool(field.extra.get("required")),
                        "description": str(field.label or name),
                        "schema": self.filter_type(model, field),
                    }
                    for name, field in filters.base_filters.items()
                    if name not in existing
                )
        self.check_operation_ids(schema)
        self.check_single_types(schema)
        return schema

    @staticmethod
    def add_page_parameters(operation: dict[str, Any], handler: Callable) -> None:
        """业务接口返回 Page[T] 时, 分页参数和资源接口的列表一样写进接口定义.

        处理函数不声明这两个参数, 由 pagination.Pagination 从请求里取, 规则和资源接口的列表一样.
        """
        returns = signature(handler, eval_str=True).return_annotation
        if not isinstance(returns, type) or not issubclass(returns, Page):
            return
        parameters = operation.setdefault("parameters", [])
        existing = {item.get("name") for item in parameters if item.get("in") == "query"}
        parameters.extend(dict(item) for item in PAGE_PARAMETERS if item["name"] not in existing)

    @staticmethod
    def filter_type(model: type[Model] | None, field: Filter) -> dict[str, str]:
        """筛选参数的类型. 数字筛选落在整数字段上时是 integer, 而不是 number.

        Returns:
            参数的 schema.

        """
        schema = FILTER_TYPES.get(type(field).__name__, {"type": "string"})
        if schema == {"type": "number"} and model is not None and field.field_name is not None:
            try:
                if isinstance(options(model).get_field(field.field_name), IntegerField):
                    return {"type": "integer"}
            except FieldDoesNotExist:
                pass
        return schema

    @staticmethod
    def check_response_type(operation: dict[str, Any], where: str) -> None:
        """业务接口必须声明返回类型 (Pydantic 模型). 不声明的话, 客户端拿到的是没有类型的对象.

        Raises:
            ImproperlyConfigured: 没有声明返回类型.

        """
        for status, response in operation.get("responses", {}).items():
            if not status.startswith("2"):
                continue
            schema = response.get("content", {}).get("application/json", {}).get("schema")
            if schema == {"type": "object"}:
                msg = f"{where} 没有声明返回类型. 给处理函数加上返回值注解, 类型是 Pydantic 模型."
                raise ImproperlyConfigured(msg)

    @staticmethod
    def check_single_types(schema: dict[str, Any]) -> None:
        """一个字段只有一种类型, 可以再加 null.

        str | int, dict | list 这样的联合类型, 每个端的生成器处理都不一样: Dart 生成不出合法的代码,
        Kotlin 和 Swift 生成的是包装类型. 需要两种形态时拆成两个字段. 有多种类型时报 ImproperlyConfigured.
        """

        def walk(node: object, where: str) -> None:
            if isinstance(node, dict):
                for key in ("anyOf", "oneOf"):
                    arms = [arm for arm in node.get(key, ()) if arm != {"type": "null"}]
                    if len(arms) > 1:
                        msg = f"{where} 有多种类型. 一个字段只能有一种类型 (可以为 null), 拆成两个字段."
                        raise ImproperlyConfigured(msg)
                kinds = node.get("type")
                if isinstance(kinds, list) and len([kind for kind in kinds if kind != "null"]) > 1:
                    msg = f"{where} 有多种类型. 一个字段只能有一种类型 (可以为 null), 拆成两个字段."
                    raise ImproperlyConfigured(msg)
                for key, value in node.items():
                    walk(value, f"{where}.{key}" if key not in {"properties", "schema", "content"} else where)
            elif isinstance(node, list):
                for item in node:
                    walk(item, where)

        for name, component in schema.get("components", {}).get("schemas", {}).items():
            walk(component, name)
        for path, item in schema["paths"].items():
            for method, operation in item.items():
                if isinstance(operation, dict):
                    walk(operation.get("parameters", []), f"{method.upper()} {path} 的参数")
                    walk(operation.get("requestBody", {}), f"{method.upper()} {path} 的请求体")
                    walk(operation.get("responses", {}), f"{method.upper()} {path} 的响应")

    @staticmethod
    def check_operation_ids(schema: dict[str, Any]) -> None:
        """接口名必须唯一: 客户端的方法名就是它.

        Raises:
            ImproperlyConfigured: 接口名重复.

        """
        seen = {}
        for path, item in schema["paths"].items():
            for method, operation in item.items():
                if not isinstance(operation, dict) or "operationId" not in operation:
                    continue
                name, where = operation["operationId"], f"{method.upper()} {path}"
                if name in seen:
                    msg = f"接口名 {name} 重复: {seen[name]} 和 {where}. 给其中一个视图类换个名字."
                    raise ImproperlyConfigured(msg)
                seen[name] = where
