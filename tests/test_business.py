"""业务接口: 幂等存下最后的响应, 分页, 错误类型和字段错误, 登录的资料类型."""

lazy from collections.abc import Iterator

import pytest
from django.core.exceptions import ImproperlyConfigured
lazy from freeman.testing import TestClient
lazy from pytest_django.fixtures import Settings

from railguns.management.commands.openapi import document
from railguns.models import IdempotencyKey
from railguns.rest_framework import auth

from .app.models import Article
from .base import bearer, user

# 带键时存下的是处理函数最后返回的响应, 而不是业务函数的返回值


@pytest.fixture
def stamp(client: TestClient) -> tuple[str, dict]:
    """用户 amy 的草稿和盖戳的接口.

    Returns:
        接口地址和带幂等键的请求头.

    """
    amy = user("amy")
    article = Article.objects.create(user_id=amy.pk, username="amy", title="draft")
    return f"/articles/{article.pk}/stamp", {**bearer(client, "amy"), "Idempotency-Key": "s-1"}


def test_the_post_processed_response_is_replayed(client: TestClient, stamp: tuple[str, dict]) -> None:
    url, headers = stamp
    first = client.post(url, json={"title": "one"}, headers=headers)
    assert first.status_code == 200, first.text
    assert sorted(first.json()) == ["id", "stamp", "title"]
    second = client.post(url, json={"title": "one"}, headers=headers)
    assert second.content == first.content  # 戳是随机的, 一样说明没有再执行
    assert bytes(IdempotencyKey.objects.get().body) == first.content


def test_a_failure_after_the_service_rolls_everything_back(client: TestClient, stamp: tuple[str, dict]) -> None:
    url, headers = stamp
    response = client.post(url, json={"title": "explode"}, headers=headers)
    assert response.status_code == 500
    assert Article.objects.get().title == "draft"  # 业务函数的写入也回滚了
    assert IdempotencyKey.objects.count() == 0
    assert client.post(url, json={"title": "two"}, headers=headers).status_code == 200


def test_without_a_key_it_is_a_plain_handler(client: TestClient, stamp: tuple[str, dict]) -> None:
    url, headers = stamp
    headers = {"Authorization": headers["Authorization"]}
    stamps = {client.post(url, json={"title": "x"}, headers=headers).json()["stamp"] for _ in range(2)}
    assert (len(stamps), IdempotencyKey.objects.count()) == (2, 0)


# 分页


@pytest.fixture
def titles(client: TestClient) -> None:
    """五篇文章, 标题 t0 到 t4."""
    for index in range(5):
        Article.objects.create(user_id=1, username="amy", title=f"t{index}")


@pytest.mark.usefixtures("titles")
def test_the_same_rules_as_a_resource_list(client: TestClient) -> None:
    first = client.get("/titles?page_size=2").json()
    assert (first["count"], [row["title"] for row in first["results"]]) == (5, ["t0", "t1"])
    assert first["next"].endswith("/titles?page_size=2&page=2")
    last = client.get("/titles?page_size=2&page=3").json()
    assert (len(last["results"]), last["next"]) == (1, None)
    assert last["previous"].endswith("/titles?page_size=2&page=2")
    assert len(client.get("/titles?page_size=100000").json()["results"]) == 5


@pytest.mark.usefixtures("titles")
@pytest.mark.parametrize("page", ["0", "4", "abc"])
def test_pages_out_of_range(client: TestClient, page: str) -> None:
    assert client.get(f"/titles?page_size=2&page={page}").status_code == 404


def test_the_parameters_are_documented() -> None:
    operation = document()["paths"]["/titles"]["get"]
    assert [item["name"] for item in operation["parameters"]] == ["page", "page_size"]


# 错误


def test_a_validation_error_lists_its_fields(client: TestClient) -> None:
    response = client.post("/articles/1/check")
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "invalid"
    assert [(item["loc"], item["type"]) for item in body["fields"]] == [(["title"], "blank")]
    assert body["detail"] == body["fields"][0]["msg"]


@pytest.mark.parametrize(("status", "code"), [(429, "rate_limited"), (502, "sms_failed"), (503, "service_unavailable")])
def test_upstream_and_rate_limit(client: TestClient, status: int, code: str) -> None:
    response = client.get(f"/upstream/{status}")
    assert (response.status_code, response.json()["code"]) == (status, code)
    assert "fields" not in response.json()


# 登录的资料类型


@pytest.fixture
def profile() -> Iterator[None]:
    """登录结果的类型按设置缓存: 测试前后都清掉.

    Yields:
        测试期间什么也不做.

    """
    auth.profile_function.cache_clear()
    auth.login_result.cache_clear()
    yield
    auth.profile_function.cache_clear()
    auth.login_result.cache_clear()


@pytest.mark.usefixtures("profile")
def test_the_response_type_has_the_profile_fields_next_to_the_tokens() -> None:
    schema = document()["components"]["schemas"]["LoginResult"]
    assert list(schema["properties"]) == ["username", "token", "access", "refresh"]
    assert "additionalProperties" not in schema


@pytest.mark.usefixtures("profile")
def test_without_a_profile_only_tokens(settings: Settings) -> None:
    settings.RAILGUNS_LOGIN_PROFILE = None
    assert list(auth.login_result().model_fields) == ["token", "access", "refresh"]


@pytest.mark.usefixtures("profile")
def test_a_profile_without_a_typed_return_is_refused(settings: Settings) -> None:
    settings.RAILGUNS_LOGIN_PROFILE = "tests.app.services.titles"
    with pytest.raises(ImproperlyConfigured, match="必须声明返回类型"):
        auth.login_result()
