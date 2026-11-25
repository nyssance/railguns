"""Idempotency-Key (draft-ietf-httpapi-idempotency-key-header)."""

import asyncio
import threading
from datetime import timedelta
from io import StringIO
from types import SimpleNamespace
from unittest import mock

import psycopg
import pytest
from django.core.management import call_command
from django.db import connection
from freeman.exceptions import HTTPException
from psycopg.conninfo import make_conninfo
from pydantic import TypeAdapter
lazy from django.contrib.auth.models import AbstractBaseUser
lazy from django.db.models import Model
lazy from freeman.testing import TestClient
lazy from httpx import Response

from railguns.management.commands.openapi import document
from railguns.models import IdempotencyKey
from railguns.rest_framework.idempotency import Claim

from .app.api import ArticleList
from .app.models import Article
from .base import bearer, user

pytestmark = pytest.mark.django_db(transaction=True)


def conninfo() -> str:
    settings = connection.settings_dict
    return make_conninfo(
        dbname=settings["NAME"],
        user=settings["USER"],
        host=settings["HOST"],
        port=settings["PORT"],
        password=settings["PASSWORD"] or None,
    )


@pytest.fixture
def amy() -> AbstractBaseUser:
    return user("amy")


# 资源的创建


class Poster:
    """带 amy 的令牌和幂等键发 POST."""

    def __init__(self, client: TestClient) -> None:
        """Amy 登录."""
        self.client = client
        self.headers = bearer(client, "amy")

    def __call__(self, body: dict, key: str = "k-1", headers: dict | None = None, path: str = "/articles") -> Response:
        """发一个请求.

        Returns:
            响应.

        """
        return self.client.post(path, json=body, headers={**(headers or self.headers), "Idempotency-Key": key})


@pytest.fixture
def post(client: TestClient, amy: AbstractBaseUser) -> Poster:
    user("bob")
    return Poster(client)


def test_a_retry_gets_the_same_response_and_creates_one_row(post: Poster) -> None:
    first = post({"title": "x"})
    second = post({"title": "x"})
    assert first.status_code == 201, first.text
    assert (second.status_code, second.content) == (201, first.content)
    assert Article.objects.count() == 1
    assert first.json()["id"] == Article.objects.get().pk


def test_the_draft_quoted_form_is_the_same_key(post: Poster) -> None:
    post({"title": "x"}, key="abc")
    assert post({"title": "x"}, key='"abc"').status_code == 201
    assert Article.objects.count() == 1


def test_the_same_key_with_another_body_is_422(post: Poster) -> None:
    post({"title": "x"})
    response = post({"title": "y"})
    assert (response.status_code, response.json()["code"]) == (422, "idempotency_key_reused")
    assert post({"title": "x"}, path="/drafts").status_code == 422  # 另一个路径也是另一个请求
    assert Article.objects.count() == 1


def test_users_have_their_own_keys(client: TestClient, post: Poster) -> None:
    assert post({"title": "x"}).status_code == 201
    assert post({"title": "x"}, headers=bearer(client, "bob")).status_code == 201
    assert sorted(Article.objects.values_list("username", flat=True)) == ["amy", "bob"]


def test_a_failed_create_leaves_nothing_and_can_be_retried(post: Poster) -> None:
    original = ArticleList.perform_create

    async def fail_after_saving(view: ArticleList, obj: Model) -> None:
        await original(view, obj)
        msg = "unexpected"
        raise RuntimeError(msg)

    with mock.patch.object(ArticleList, "perform_create", fail_after_saving):
        assert post({"title": "x"}).status_code == 500
    keys = IdempotencyKey.objects.count()
    assert (Article.objects.count(), keys) == (0, 0)  # 写入的行也回滚了
    assert post({"title": "x"}).status_code == 201
    assert Article.objects.count() == 1


def test_without_the_header_nothing_changes(client: TestClient, post: Poster) -> None:
    for _ in range(2):
        assert client.post("/articles", json={"title": "x"}, headers=post.headers).status_code == 201
    keys = IdempotencyKey.objects.count()
    assert (Article.objects.count(), keys) == (2, 0)


@pytest.mark.parametrize("key", ["", '""', "x" * 256])
def test_an_invalid_key_is_400(client: TestClient, post: Poster, key: str) -> None:
    response = client.post("/articles", json={"title": "x"}, headers={**post.headers, "Idempotency-Key": key})
    assert (response.status_code, response.json()["code"]) == (400, "invalid_idempotency_key")
    assert Article.objects.count() == 0


def test_concurrent_duplicates_create_one_row(post: Poster) -> None:
    original = ArticleList.perform_create

    async def slow(view: ArticleList, obj: Model) -> None:
        await original(view, obj)
        await asyncio.sleep(0.3)

    responses: list[Response] = []
    barrier = threading.Barrier(4)

    def send() -> None:
        barrier.wait()
        responses.append(post({"title": "x"}))

    with mock.patch.object(ArticleList, "perform_create", slow):
        threads = [threading.Thread(target=send) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    assert Article.objects.count() == 1
    assert {response.status_code for response in responses} <= {201, 409}
    assert len({response.content for response in responses if response.status_code == 201}) == 1


def test_a_request_in_progress_is_409(post: Poster, amy: AbstractBaseUser) -> None:
    # 另一个连接拿着这个键的锁, 就像同一个键的第一次请求正在处理
    with psycopg.connect(conninfo()) as other:
        other.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", [f"{amy.pk}:k-1"])
        response = post({"title": "x"})
        assert (response.status_code, response.json()["code"]) == (409, "idempotency_key_in_use")
    assert post({"title": "x"}).status_code == 201  # 锁随事务释放
    assert Article.objects.count() == 1


@pytest.mark.usefixtures("post")
def test_the_unique_constraint_is_the_guarantee(amy: AbstractBaseUser) -> None:
    """锁之外, 另一个事务先提交了同一个键: 这次的插入违反唯一约束, 连同它写入的行一起回滚."""
    claim = Claim(
        SimpleNamespace(
            context={"user_id": amy.pk}, headers={"idempotency-key": "k-9"}, method="POST", path="/articles", body=b"{}"
        ),
        TypeAdapter(dict),
        201,
    )

    def work() -> dict:
        Article.objects.create(user_id=amy.pk, username="amy", title="raced")
        with psycopg.connect(conninfo(), autocommit=True) as other:
            other.execute(
                "INSERT INTO railguns_idempotencykey (user_id, key, fingerprint, status_code, body, "
                "created_time) VALUES (%s, 'k-9', 'f', 201, '', now())",
                [amy.pk],
            )
        return {}

    with pytest.raises(HTTPException) as caught:
        claim.atomic(work)
    assert caught.value.status_code == 409
    assert not Article.objects.filter(title="raced").exists()


def test_keys_expire_after_24_hours(post: Poster) -> None:
    keys = IdempotencyKey.objects
    post({"title": "x"})
    keys.update(created_time=keys.get().created_time - timedelta(hours=25))
    assert post({"title": "x"}).status_code == 201
    assert Article.objects.count() == 2  # 过期的键当作没用过
    keys.update(created_time=keys.get().created_time - timedelta(hours=25))
    post({"title": "y"}, key="k-2")
    out = StringIO()
    call_command("clearidempotencykeys", stdout=out)
    assert "删掉了 1 个" in out.getvalue()
    assert list(keys.values_list("key", flat=True)) == ["k-2"]


def test_an_anonymous_request_with_a_key_is_401() -> None:
    request = SimpleNamespace(context=None, headers={"idempotency-key": "k"}, method="POST", path="/", body=b"")
    with pytest.raises(HTTPException) as caught:
        Claim.of(request, TypeAdapter(dict), 201)
    assert caught.value.status_code == 401


# 业务动作


@pytest.fixture
def draft(amy: AbstractBaseUser) -> Article:
    return Article.objects.create(user_id=amy.pk, username="amy", title="draft")


@pytest.fixture
def headers(client: TestClient, amy: AbstractBaseUser) -> dict:
    return {**bearer(client, "amy"), "Idempotency-Key": "p-1"}


def test_a_retry_does_not_run_the_service_again(client: TestClient, draft: Article, headers: dict) -> None:
    url = f"/articles/{draft.pk}/publish"
    first = client.post(url, json={"title": "one"}, headers=headers)
    assert first.json() == {"id": draft.pk, "title": "one"}
    Article.objects.filter(pk=draft.pk).update(title="changed meanwhile")
    second = client.post(url, json={"title": "one"}, headers=headers)
    assert (second.status_code, second.content) == (first.status_code, first.content)
    assert Article.objects.get(pk=draft.pk).title == "changed meanwhile"
    other = client.post(url, json={"title": "two"}, headers=headers)
    assert (other.status_code, other.json()["code"]) == (422, "idempotency_key_reused")


def test_a_business_error_is_not_stored(client: TestClient, draft: Article, headers: dict) -> None:
    response = client.post(f"/articles/{draft.pk}/publish", json={"title": "dup"}, headers=headers)
    assert (response.status_code, response.json()["code"]) == (409, "published")
    assert Article.objects.get(pk=draft.pk).title == "draft"  # 业务函数的写入回滚了
    assert IdempotencyKey.objects.count() == 0


def test_the_business_action_without_the_header(client: TestClient, draft: Article, headers: dict) -> None:
    authorization = {"Authorization": headers["Authorization"]}
    for title in ("a", "b"):
        response = client.post(f"/articles/{draft.pk}/publish", json={"title": title}, headers=authorization)
        assert response.json()["title"] == title
    assert IdempotencyKey.objects.count() == 0


# 接口文档


def test_the_header_is_documented_on_the_idempotent_operations() -> None:
    schema = document()
    found = {
        f"{method.upper()} {path}"
        for path, item in schema["paths"].items()
        for method, operation in item.items()
        if any(p["name"] == "Idempotency-Key" and p["in"] == "header" for p in operation.get("parameters", []))
    }
    assert found == {
        "POST /articles",
        "POST /drafts",
        "POST /notes",
        "POST /posts",
        "POST /articles/{pk}/publish",
        "POST /articles/{pk}/stamp",
    }
