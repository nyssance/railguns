"""OpenAPI 文档, 序列化器的字段混入, Bolt 的内部函数."""

import datetime as dt
from types import SimpleNamespace

import pytest
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from freeman.openapi import OpenAPIConfig

from railguns.rest_framework import _bolt, mixins
from railguns.rest_framework.schemas.openapi import AutoSchema

from .app.api import api

MEDIA = SimpleNamespace(
    images=" a.png\n\n b.png ", tags="one## two ", start_time=dt.datetime(2025, 2, 1, 12, tzinfo=dt.UTC), period=2
)


@pytest.fixture(scope="module")
def paths() -> dict:
    """生成一次 OpenAPI 文档.

    Returns:
        文档的 paths.

    """
    return AutoSchema(api, OpenAPIConfig(title="Test", version="v1")).generate()["paths"]


def test_operation_ids_are_model_plus_action(paths: dict) -> None:
    assert paths["/articles"]["get"]["operationId"] == "ArticlesList"
    assert paths["/articles"]["post"]["operationId"] == "ArticleCreate"
    assert paths["/articles/{pk}"]["get"]["operationId"] == "ArticleRetrieve"
    assert paths["/articles/{pk}"]["patch"]["operationId"] == "ArticlePartialUpdate"


def test_tags(paths: dict) -> None:
    assert paths["/articles"]["get"]["tags"] == ["articles"]
    assert paths["/articles/{pk}"]["get"]["tags"] == ["articles"]


def test_filters_are_documented_on_lists_only(paths: dict) -> None:
    names = {parameter["name"] for parameter in paths["/articles"]["get"]["parameters"]}
    assert {"score", "username"} <= names
    detail = {parameter["name"] for parameter in paths["/articles/{pk}"]["get"].get("parameters", [])}
    assert not {"score", "username"} & detail


def test_images_and_tags() -> None:
    assert mixins.ImagesFieldMixin().get_images(MEDIA).model_dump() == {
        "count": 2,
        "data": [{"uri": "a.png"}, {"uri": "b.png"}],
    }
    assert mixins.TagsFieldMixin().get_tags(MEDIA) == ["one", "two"]
    with pytest.raises(AttributeError):  # 模型上没有这个字段是声明错了, 不返回提示字符串
        mixins.TagsFieldMixin().get_tags(object())


def test_dates() -> None:
    with timezone.override(dt.UTC):
        assert mixins.StartDateFieldMixin().get_start_date(MEDIA) == "2025-02-01"
        assert mixins.EndDateFieldMixin().get_end_date(MEDIA) == "2025-02-02"
        assert mixins.EndDateFieldMixin().get_end_date(SimpleNamespace(period=0)) == ""


def test_password() -> None:
    assert check_password("abc12345", mixins.PasswordFieldMixin().validate_password("abc12345"))
    with pytest.raises(ValidationError):
        mixins.PasswordFieldMixin().validate_password("short")


def test_routes() -> None:
    routes = _bolt.routes(api)
    assert ("POST", "/api/v1/auth/login") in [(method, path) for method, path, _ in routes]
