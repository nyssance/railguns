"""manage.py openapi: 导出, 一致性检查, 破坏性变更检查."""

import copy
import json
import re
import shutil
from io import StringIO
lazy from collections.abc import Callable
lazy from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from freeman.openapi import OpenAPIConfig

from railguns.management.commands.openapi import document, dumps
from railguns.rest_framework.schemas.openapi import AutoSchema

from .app.api import api

needs_oasdiff = pytest.mark.skipif(not shutil.which("oasdiff"), reason="需要 oasdiff")


@pytest.fixture(scope="module")
def schema() -> dict:
    """导出一次接口定义.

    Returns:
        接口定义.

    """
    return document()


# 导出的文档


def test_names_are_unique_and_fixed(schema: dict) -> None:
    names = [operation["operationId"] for item in schema["paths"].values() for operation in item.values()]
    assert len(names) == len(set(names))
    assert {"ArticlesList", "ArticleCreate", "ArticleRetrieve", "Login", "UploadParams"} <= set(names)
    # 五个资源类的每个动作: ListCreateAPI, RetrieveUpdateAPI, CreateAPI, ListAPI, RetrieveAPI
    assert {
        "ArticleUpdate",
        "ArticlePartialUpdate",
        "DraftCreate",
        "ReadOnlyArticlesList",
        "ReadOnlyArticleRetrieve",
    } <= set(names)
    assert not [path for path, item in schema["paths"].items() if "delete" in item]


def test_lists_document_their_page_parameters(schema: dict) -> None:
    parameters = {item["name"]: item["schema"] for item in schema["paths"]["/articles"]["get"]["parameters"]}
    assert parameters["page"] == {"type": "integer", "minimum": 1, "default": 1}
    assert parameters["page_size"]["maximum"] == 1000
    assert parameters["score"] == {"type": "integer"}  # 整数字段的筛选是 integer, 不是 number


def test_every_response_is_typed(schema: dict) -> None:
    for path, item in schema["paths"].items():
        for method, operation in item.items():
            responses = operation["responses"]
            body = responses.get("200", responses.get("201"))["content"]["application/json"]
            assert "$ref" in body["schema"], f"{method} {path}"


def test_no_field_has_two_types(schema: dict) -> None:
    text = json.dumps(schema)
    assert '"anyOf"' not in text
    assert '"oneOf"' not in text


def test_fields_keep_their_declared_order(schema: dict) -> None:
    credentials = schema["components"]["schemas"]["Credentials"]
    assert list(credentials["properties"]) == ["username", "password"]


def test_the_export_is_reproducible() -> None:
    assert dumps(document()) == dumps(document())


# 规则


def test_a_field_with_two_types_is_refused() -> None:
    schema = {
        "paths": {},
        "components": {
            "schemas": {"Thing": {"properties": {"value": {"anyOf": [{"type": "string"}, {"type": "integer"}]}}}}
        },
    }
    with pytest.raises(ImproperlyConfigured, match=re.escape("Thing.value 有多种类型")):
        AutoSchema.check_single_types(schema)


def test_a_nullable_field_is_allowed() -> None:
    schema = {"paths": {}, "components": {"schemas": {"Thing": {"properties": {"name": {"type": ["string", "null"]}}}}}}
    AutoSchema.check_single_types(schema)


def test_a_business_endpoint_without_a_return_type_is_refused() -> None:
    operation = {"responses": {"200": {"content": {"application/json": {"schema": {"type": "object"}}}}}}
    with pytest.raises(ImproperlyConfigured, match="没有声明返回类型"):
        AutoSchema.check_response_type(operation, "GET /things")


def test_duplicate_names_are_refused() -> None:
    schema = {"paths": {"/a": {"get": {"operationId": "Same"}}, "/b": {"get": {"operationId": "Same"}}}}
    with pytest.raises(ImproperlyConfigured, match="接口名 Same 重复"):
        AutoSchema.check_operation_ids(schema)


def test_the_generated_document_passes_as_a_whole() -> None:
    AutoSchema(api, OpenAPIConfig(title="t", version="v1")).generate()


# 命令


@pytest.fixture
def path(tmp_path: Path) -> Path:
    """导出文件的位置.

    Returns:
        临时目录里的 openapi.json.

    """
    return tmp_path / "openapi.json"


def run_command(path: Path, *args: str) -> str:
    """运行 openapi 命令.

    Returns:
        命令的输出.

    """
    out = StringIO()
    call_command("openapi", "--out", str(path), *args, stdout=out)
    return out.getvalue()


def base_with(path: Path, change: Callable[[dict], None]) -> str:
    """一份旧的接口定义: 现在的定义经过 change 改动.

    Returns:
        它的路径.

    """
    old = copy.deepcopy(document())
    change(old)
    base = path.with_name("base.json")
    base.write_text(dumps(old))
    return str(base)


def test_export_then_check(path: Path) -> None:
    assert "已写入" in run_command(path)
    assert json.loads(path.read_text(encoding="utf-8"))["openapi"][:3] == "3.1"
    assert "一致" in run_command(path, "--check")


def test_check_fails_when_the_file_is_missing_or_stale(path: Path) -> None:
    with pytest.raises(CommandError, match="和代码不一致"):
        run_command(path, "--check")
    run_command(path)
    path.write_text(path.read_text(encoding="utf-8").replace("ArticlesList", "Renamed"), encoding="utf-8")
    with pytest.raises(CommandError, match="和代码不一致"):
        run_command(path, "--check")


@needs_oasdiff
def test_no_breaking_change_against_itself(path: Path) -> None:
    assert "没有破坏性变更" in run_command(path, "--breaking", base_with(path, lambda _: None))


@needs_oasdiff
def test_a_new_optional_field_is_not_breaking(path: Path) -> None:
    def change(old: dict) -> None:  # 旧定义里没有 summary: 相当于现在新增了一个响应字段
        del old["components"]["schemas"]["ArticleSerializer"]["properties"]["summary"]
        old["components"]["schemas"]["ArticleSerializer"]["required"].remove("summary")

    assert "没有破坏性变更" in run_command(path, "--breaking", base_with(path, change))


@needs_oasdiff
def test_a_removed_response_field_is_breaking(path: Path) -> None:
    def change(old: dict) -> None:  # 旧定义里有 nickname: 相当于现在把它删了
        article = old["components"]["schemas"]["ArticleSerializer"]
        article["properties"]["nickname"] = {"type": "string"}
        article["required"].append("nickname")

    with pytest.raises(CommandError, match="有破坏性变更"):
        run_command(path, "--breaking", base_with(path, change))


@needs_oasdiff
def test_a_removed_endpoint_is_breaking(path: Path) -> None:
    def change(old: dict) -> None:
        old["paths"]["/articles/{pk}/archive"] = copy.deepcopy(old["paths"]["/whoami"])
        old["paths"]["/articles/{pk}/archive"]["get"]["operationId"] = "Archive"

    with pytest.raises(CommandError, match="有破坏性变更"):
        run_command(path, "--breaking", base_with(path, change))


@needs_oasdiff
def test_a_new_required_request_field_is_breaking(path: Path) -> None:
    def change(old: dict) -> None:  # 旧定义里 title 不是必填: 相当于现在把它改成了必填
        old["components"]["schemas"]["ArticleInput"]["required"].remove("title")

    with pytest.raises(CommandError, match="有破坏性变更"):
        run_command(path, "--breaking", base_with(path, change))


@needs_oasdiff
def test_a_base_that_is_neither_a_file_nor_a_commit(path: Path) -> None:
    with pytest.raises(CommandError, match="既不是文件"):
        run_command(path, "--breaking", "no-such-commit-or-file")
