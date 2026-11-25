"""创建: Django 的 ORM 照常保存 (信号, save(), db_default 都生效). 响应体就是随后 GET 的结果, 所有者取自令牌."""

import logging
import threading
from contextlib import contextmanager
from logging.handlers import BufferingHandler
from types import SimpleNamespace
from unittest import mock
lazy from collections.abc import Generator

import psycopg
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.signals import post_save
lazy from django.contrib.auth.models import AbstractBaseUser, User
lazy from django.db.models import Model
lazy from freeman.testing import TestClient
lazy from pydantic import BaseModel

from railguns.models import IdempotencyKey
from railguns.rest_framework.generics import ListCreateAPI, conflict, unique_constraints

from .app.api import PostList
from .app.models import Article, LoudArticle, Note, Post
from .app.serializers import ArticleInput, ArticleSerializer, NoteInput, NoteSerializer, PostInput
from .base import bearer, user

pytestmark = pytest.mark.django_db(transaction=True)


@contextmanager
def queries() -> Generator[list[tuple[str, str]]]:
    """这段时间里所有线程在 ORM 连接上执行的语句, 每条记下 (线程名, SQL).

    处理函数在引擎的线程里用自己的连接, 测试线程的 CaptureQueriesContext 看不到, 所以在驱动这一层记.

    Yields:
        执行过的语句.

    """
    executed: list[tuple[str, str]] = []
    execute = psycopg.Cursor.execute

    def recorded(cursor: psycopg.Cursor, query: object, *args: object, **kwargs: object) -> psycopg.Cursor:
        executed.append((threading.current_thread().name, str(query)))
        return execute(cursor, query, *args, **kwargs)

    with mock.patch.object(psycopg.Cursor, "execute", recorded):
        yield executed


@contextmanager
def errors_logged() -> Generator[None]:
    """这段时间里 django.request 至少记了一条 ERROR, 和 assertLogs 一样.

    Yields:
        记录期间什么也不做.

    """
    handler = BufferingHandler(1000)
    handler.setLevel(logging.ERROR)
    logger = logging.getLogger("django.request")
    logger.addHandler(handler)
    try:
        yield
    finally:
        logger.removeHandler(handler)
    assert handler.buffer, "django.request 没有记 ERROR"


class StampedNotes(ListCreateAPI):
    """覆盖了 perform_create."""

    model = Note
    serializer_class = NoteSerializer
    input_class = NoteInput

    def perform_create(self, obj: Model) -> None:
        assert isinstance(obj, Note)
        obj.title += "!"
        super().perform_create(obj)


class LoudArticles(ListCreateAPI):
    """模型覆盖了 save()."""

    model = LoudArticle
    serializer_class = ArticleSerializer
    input_class = ArticleInput


def create(view: type[ListCreateAPI], data: BaseModel, user_id: str | None = None) -> object:
    """不经过引擎, 在测试线程里直接调用处理函数.

    Returns:
        处理函数返回的对象.

    """
    users = get_user_model().objects
    request = SimpleNamespace(
        context={"user_id": user_id} if user_id else {},
        headers={},
        method="POST",
        user=users.filter(pk=user_id).first() if user_id else None,
    )
    return view.as_handler("create", "/x", 201)(request, data=data)


@pytest.fixture
def amy() -> User:
    return user("amy")


@pytest.fixture
def headers(client: TestClient, amy: AbstractBaseUser) -> dict:
    return bearer(client, "amy")


def test_the_body_is_the_following_get(client: TestClient, amy: AbstractBaseUser, headers: dict) -> None:
    for title in ("a", "b"):
        response = client.post("/notes", json={"title": title, "user_id": 999}, headers=headers)
        assert response.status_code == 201, response.text
        body = response.json()
        assert (body["title"], body["rank"], body["user_id"], body["is_active"]) == (title, 7, amy.pk, True)
        assert response.content == client.get(f"/notes/{body["id"]}").content
    assert Note.objects.count() == 2


def test_the_owner_comes_from_the_token(client: TestClient, amy: AbstractBaseUser, headers: dict) -> None:
    response = client.post("/articles", json={"title": "a"}, headers=headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert (body["user_id"], body["username"]) == (amy.pk, "amy")
    assert body == client.get(f"/articles/{body["id"]}").json()


def test_queries_run_on_the_executor_thread(client: TestClient, headers: dict) -> None:
    """生成的处理函数在引擎的线程池 (bolt_default_*) 里执行, 不在事件循环的线程上. 每个请求的查询条数.

    创建: 读用户 (所有者字段), INSERT. 列表: 这一页的行, 总数. 详情: 一条.
    """
    with queries() as created:
        response = client.post("/articles", json={"title": "a"}, headers=headers)
    assert response.status_code == 201, response.text
    with queries() as listed:
        assert client.get("/articles").status_code == 200
    with queries() as retrieved:
        assert client.get(f"/articles/{response.json()["id"]}").status_code == 200
    for executed, count in ((created, 2), (listed, 2), (retrieved, 1)):
        assert len(executed) == count, executed
        assert all(thread.startswith("bolt_default") for thread, _ in executed), executed
    assert created[1][1].startswith("INSERT INTO")


def test_a_user_that_is_gone_or_inactive_creates_nothing(client: TestClient, amy: User, headers: dict) -> None:
    amy.is_active = False
    amy.save()
    for path in ("/notes", "/articles"):
        response = client.post(path, json={"title": path}, headers=headers)
        assert (response.status_code, response.json()["code"]) == (401, "not_authenticated"), path
    amy.delete()
    assert client.post("/notes", json={"title": "x"}, headers=headers).status_code == 401
    assert (Note.objects.count(), Article.objects.count()) == (0, 0)


def test_a_unique_violation_is_409_and_other_integrity_errors_are_500(
    client: TestClient, amy: AbstractBaseUser, headers: dict
) -> None:
    Note.objects.create(user_id=amy.pk, title="taken")
    with errors_logged():
        taken = client.post("/notes", json={"title": "taken"}, headers=headers)
        negative = client.post("/posts", json={"title": "p", "category_id": -1}, headers=headers)
    assert taken.status_code == 409
    assert taken.json() == {
        "code": "conflict",
        "detail": "已经存在相同的记录。",
        "fields": [{"loc": ["title"], "msg": "这个值已经存在。", "type": "unique"}],
    }
    # 别的完整性错误 (这里是检查约束: id 列不能是负数) 不是 409, 照旧是 500
    assert negative.status_code == 500
    with errors_logged(), pytest.raises(IntegrityError) as raised:
        create(PostList, PostInput(title="p", category_id=-1), str(amy.pk))
    assert isinstance(raised.value.__cause__, psycopg.errors.CheckViolation)
    assert (Note.objects.count(), Post.objects.count()) == (1, 0)


def test_an_update_to_a_taken_value_is_409(client: TestClient, amy: AbstractBaseUser, headers: dict) -> None:
    Note.objects.create(user_id=amy.pk, title="taken")
    mine = Note.objects.create(user_id=amy.pk, title="mine")
    response = client.patch(f"/notes/{mine.pk}", json={"title": "taken"}, headers=headers)
    assert response.status_code == 409, response.text
    assert response.json()["fields"] == [{"loc": ["title"], "msg": "这个值已经存在。", "type": "unique"}]
    Note.objects.filter(pk=mine.pk).update(title="mine")
    assert Note.objects.get(pk=mine.pk).title == "mine"


@pytest.mark.usefixtures("headers")
def test_a_constraint_that_is_not_known_has_no_fields() -> None:
    cause = Exception("duplicate")
    cause.sqlstate, cause.diag = "23505", SimpleNamespace(constraint_name="somewhere_else")
    exc = IntegrityError("duplicate")
    exc.__cause__ = cause
    error = conflict(Note, exc)
    assert error is not None
    assert "fields" not in (error.extra or {})
    assert error.status_code == 409
    assert unique_constraints(Note, "default")["app_note_pkey"] == ["id"]


# Django 的写法照常生效: 覆盖的方法, save(), 信号


def test_an_overridden_perform_create(amy: AbstractBaseUser) -> None:
    obj = create(StampedNotes, NoteInput(title="a"), str(amy.pk))
    assert isinstance(obj, Note)
    assert (obj.title, obj.user_id, obj.rank) == ("a!", amy.pk, 7)
    assert Note.objects.filter(title="a!", user_id=amy.pk).exists()


def test_a_model_with_a_custom_save(amy: AbstractBaseUser) -> None:
    obj = create(LoudArticles, ArticleInput(title="a"), str(amy.pk))
    assert isinstance(obj, Article)
    assert obj.summary == "saved"
    assert Article.objects.get(pk=obj.pk).summary == "saved"


@pytest.mark.usefixtures("amy")
def test_a_model_with_a_post_save_receiver(client: TestClient) -> None:
    received = []

    def receiver(instance: Note, created: bool, **_: object) -> None:
        received.append((instance.title, created))

    post_save.connect(receiver, sender=Note)
    try:
        response = client.post("/notes", json={"title": "a"}, headers=bearer(client, "amy"))
    finally:
        post_save.disconnect(receiver, sender=Note)
    assert response.status_code == 201, response.text
    assert received == [("a", True)]
    assert response.json() == client.get(f"/notes/{response.json()["id"]}").json()


@pytest.mark.usefixtures("amy")
def test_an_idempotent_create(client: TestClient) -> None:
    headers = {**bearer(client, "amy"), "Idempotency-Key": "k-1"}
    first = client.post("/notes", json={"title": "a"}, headers=headers)
    second = client.post("/notes", json={"title": "a"}, headers=headers)
    assert first.status_code == 201, first.text
    assert (second.status_code, second.content) == (201, first.content)
    assert Note.objects.count() == 1
    assert first.json() == client.get(f"/notes/{first.json()["id"]}").json()
    taken = client.post("/notes", json={"title": "a"}, headers={**headers, "Idempotency-Key": "k-2"})
    assert (taken.status_code, taken.json()["code"]) == (409, "conflict")  # 键的事务回滚, 可以重试
    assert not IdempotencyKey.objects.filter(key="k-2").exists()
