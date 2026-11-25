"""railguns.testing 的工具: 权限矩阵, 序列化器契约, 快照."""

import json
import tempfile
from pathlib import Path
from unittest import TestCase

import pytest
lazy from freeman.testing import TestClient

from railguns.testing import access_matrix, check_snapshot, serializer_contract
from railguns.testing.matrix import sample_path

from .app import serializers
from .app.api import api
from .app.models import Article
from .base import bearer, user


def test_every_route_and_actor(client: TestClient) -> None:
    amy = user("amy")
    Article.objects.create(pk=1, user_id=amy.pk, username="amy", title="t")
    matrix = access_matrix(api, {"anonymous": {}, "amy": bearer(client, "amy")}, client=client)
    assert matrix["GET /articles"] == {"anonymous": 200, "amy": 200}
    assert matrix["POST /articles"] == {"anonymous": 401, "amy": 422}  # 先判断权限, 再校验参数
    assert matrix["POST /articles/1/publish"] == {"anonymous": 401, "amy": 422}
    assert matrix["GET /users/1/articles"]["anonymous"] == 401
    routes = {(method, path) for method, path, *_ in api._routes}
    assert len(matrix) == len(routes) - 2  # 登出的两个不在矩阵里
    assert "POST /api/v1/auth/logout" not in matrix
    assert matrix["PATCH /articles/1"] == {"anonymous": 401, "amy": 200}


def test_only_selected_methods(client: TestClient) -> None:
    matrix = access_matrix(api, {"anonymous": {}}, methods=("GET",), client=client)
    assert all(key.startswith("GET ") for key in matrix)


def test_sample_path() -> None:
    assert sample_path("/orders/{pk}/files/{name:path}") == "/orders/1/files/sample"


def test_fields() -> None:
    contract = serializer_contract(serializers)
    fields = contract["tests.app.serializers.ArticleSerializer"]
    assert fields["title"] == {"type": "str", "required": True, "computed": False}
    assert fields["tag_list"]["computed"] is True
    writable = contract["tests.app.serializers.ArticleInput"]
    assert writable["summary"]["required"] is False
    assert "id" not in writable  # 请求体里没有主键
    assert "tests.app.serializers.Publish" in contract


def test_record_then_compare() -> None:
    case = TestCase()  # check_snapshot 用 unittest 的 fail 和 assertEqual 报告
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "nested" / "matrix.json"
        with pytest.raises(AssertionError, match="不存在, 已写入"):  # 第一次: 写入快照并让测试失败, 提醒检查后提交
            check_snapshot(case, path, {"GET /a": {"anonymous": 200}})
        assert json.loads(path.read_text()) == {"GET /a": {"anonymous": 200}}
        check_snapshot(case, path, {"GET /a": {"anonymous": 200}})
        with pytest.raises(AssertionError):
            check_snapshot(case, path, {"GET /a": {"anonymous": 401}})
