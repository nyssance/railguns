"""创建: 一条 INSERT ... RETURNING 在原生连接上执行; 不能的时候 (信号, save(), 覆盖的方法, 幂等键) 照旧走 ORM."""

import logging
from contextlib import contextmanager
from logging.handlers import BufferingHandler
from types import SimpleNamespace
from unittest import mock
lazy from collections.abc import Generator

import psycopg
import pytest
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.signals import post_save
from freeman.postgres import close_pools
lazy from django.contrib.auth.models import AbstractBaseUser, User
lazy from django.db.models import Model
lazy from freeman.testing import TestClient
lazy from pydantic import BaseModel

from railguns.models import IdempotencyKey
from railguns.rest_framework import generics
from railguns.rest_framework.generics import STATEMENTS, ListCreateAPI, Statement, conflict, unique_constraints

from .app.api import ArticleList, NoteList, PostList
from .app.models import Article, LoudArticle, Note, Post
from .app.serializers import ArticleInput, ArticleSerializer, NoteInput, NoteSerializer, PostInput
from .base import bearer, user

pytestmark = pytest.mark.django_db(transaction=True)


@contextmanager
def statements() -> Generator[dict[str, list[str]]]:
    """这段时间里执行的语句: native 是原生连接上的, orm 是 ORM 连接上的 (所有线程).

    Yields:
        两种连接上执行过的语句.

    """
    executed: dict[str, list[str]] = {"native": [], "orm": []}
    native, orm = generics.execute, psycopg.Cursor.execute

    async def counted(statement: Statement) -> list[tuple]:
        executed["native"].append(statement[1])
        return await native(statement)

    def recorded(cursor: psycopg.Cursor, query: object, *args: object, **kwargs: object) -> psycopg.Cursor:
        executed["orm"].append(str(query))
        return orm(cursor, query, *args, **kwargs)

    with mock.patch.object(generics, "execute", counted), mock.patch.object(psycopg.Cursor, "execute", recorded):
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


def ignore(**kwargs: object) -> None:
    """什么也不做的信号接收函数: 有接收函数, 创建就走 ORM."""


@contextmanager
def receivers(*senders: type[Model]) -> Generator[None]:
    """这段时间里给这些模型连上 post_save 的接收函数.

    Yields:
        连着接收函数的期间.

    """
    for sender in senders:
        post_save.connect(ignore, sender=sender)
    try:
        yield
    finally:
        for sender in senders:
            post_save.disconnect(ignore, sender=sender)


class StampedNotes(ListCreateAPI):
    """覆盖了 perform_create: 走 ORM."""

    model = Note
    serializer_class = NoteSerializer
    input_class = NoteInput

    async def perform_create(self, obj: Model) -> None:
        assert isinstance(obj, Note)
        obj.title += "!"
        await super().perform_create(obj)


class LoudArticles(ListCreateAPI):
    """模型覆盖了 save(): 走 ORM."""

    model = LoudArticle
    serializer_class = ArticleSerializer
    input_class = ArticleInput


def create(view: type[ListCreateAPI], data: BaseModel, user_id: str | None = None) -> object:
    """不经过引擎直接调用处理函数. 这个事件循环的原生连接池用完就关掉.

    Returns:
        处理函数返回的对象.

    """

    async def auser() -> AbstractBaseUser:
        return await get_user_model().objects.aget(pk=user_id)

    request = SimpleNamespace(context={"user_id": user_id} if user_id else {}, headers={}, method="POST", auser=auser)
    handler = view.as_handler("create", "/x", 201)

    async def call() -> object:
        try:
            return await handler(request, data=data)
        finally:
            await close_pools()

    return async_to_sync(call)()


@pytest.fixture
def amy() -> User:
    return user("amy")


@pytest.fixture
def headers(client: TestClient, amy: AbstractBaseUser) -> dict:
    STATEMENTS.clear()
    return bearer(client, "amy")


# 原生创建


def test_the_body_is_the_following_get(client: TestClient, amy: AbstractBaseUser, headers: dict) -> None:
    for title in ("a", "b"):  # 第二次用记下的 INSERT
        response = client.post("/notes", json={"title": title, "user_id": 999}, headers=headers)
        assert response.status_code == 201, response.text
        body = response.json()
        assert (body["title"], body["rank"], body["user_id"], body["is_active"]) == (title, 7, amy.pk, True)
        assert response.content == client.get(f"/notes/{body["id"]}").content
    assert len([key for key in STATEMENTS.entries if key[:2] == (NoteList, "create")]) == 1
    assert Note.objects.count() == 2


def test_one_statement_and_no_user_query(client: TestClient, headers: dict) -> None:
    with statements() as executed:
        response = client.post("/notes", json={"title": "a"}, headers=headers)
    assert response.status_code == 201, response.text
    assert executed["orm"] == []
    [insert] = executed["native"]
    assert insert.startswith("INSERT INTO"), insert
    assert "RETURNING" in insert


def test_the_username_is_read_in_the_same_statement(client: TestClient, amy: AbstractBaseUser, headers: dict) -> None:
    for title in ("a", "b"):  # 第二次用记下的语句
        with statements() as executed:
            response = client.post("/articles", json={"title": title}, headers=headers)
        assert response.status_code == 201, response.text
        assert executed["orm"] == []
        [insert] = executed["native"]
        assert "auth_user" in insert
        body = response.json()
        assert (body["user_id"], body["username"]) == (amy.pk, "amy")
        assert body == client.get(f"/articles/{body["id"]}").json()


def test_a_user_that_is_gone_or_inactive_creates_nothing(client: TestClient, amy: User, headers: dict) -> None:
    amy.is_active = False
    amy.save()
    for path in ("/notes", "/articles"):
        response = client.post(path, json={"title": path}, headers=headers)
        assert (response.status_code, response.json()["code"]) == (401, "not_authenticated"), path
        with receivers(Note, Article):  # 走 ORM 也一样
            orm = client.post(path, json={"title": path}, headers=headers)
        assert (orm.status_code, orm.content) == (response.status_code, response.content), path
    amy.delete()
    assert client.post("/notes", json={"title": "x"}, headers=headers).status_code == 401
    assert (Note.objects.count(), Article.objects.count()) == (0, 0)


def test_integrity_errors_are_the_same_as_through_the_orm(
    client: TestClient, amy: AbstractBaseUser, headers: dict
) -> None:
    Note.objects.create(user_id=amy.pk, title="taken")
    with errors_logged():
        native = client.post("/notes", json={"title": "taken"}, headers=headers)
        negative = client.post("/posts", json={"title": "p", "category_id": -1}, headers=headers)
        with receivers(Note, Post):
            orm = client.post("/notes", json={"title": "taken"}, headers=headers)
            orm_negative = client.post("/posts", json={"title": "p", "category_id": -1}, headers=headers)
    assert (native.status_code, native.content) == (orm.status_code, orm.content)
    assert native.status_code == 409
    assert native.json() == {
        "code": "conflict",
        "detail": "已经存在相同的记录。",
        "fields": [{"loc": ["title"], "msg": "这个值已经存在。", "type": "unique"}],
    }
    # 别的完整性错误 (这里是检查约束: id 列不能是负数) 不是 409, 照旧是 500
    assert (negative.status_code, negative.content) == (orm_negative.status_code, orm_negative.content)
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


# 这些创建照旧走 ORM: 原生连接上没有 INSERT.


@pytest.mark.parametrize(
    ("view", "native"),
    [(NoteList, True), (ArticleList, True), (PostList, True), (StampedNotes, False), (LoudArticles, False)],
)
def test_the_decision(view: type[ListCreateAPI], native: bool) -> None:
    assert view.native_create() is native


def test_an_overridden_perform_create(amy: AbstractBaseUser) -> None:
    with statements() as executed:
        obj = create(StampedNotes, NoteInput(title="a"), str(amy.pk))
    assert executed["native"] == []
    assert isinstance(obj, Note)
    assert (obj.title, obj.user_id, obj.rank) == ("a!", amy.pk, 7)
    assert Note.objects.filter(title="a!", user_id=amy.pk).exists()


def test_a_model_with_a_custom_save(amy: AbstractBaseUser) -> None:
    with statements() as executed:
        obj = create(LoudArticles, ArticleInput(title="a"), str(amy.pk))
    assert executed["native"] == []
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
        with statements() as executed:
            response = client.post("/notes", json={"title": "a"}, headers=bearer(client, "amy"))
    finally:
        post_save.disconnect(receiver, sender=Note)
    assert response.status_code == 201, response.text
    assert not any(sql.startswith("INSERT") for sql in executed["native"])
    assert received == [("a", True)]
    assert response.json() == client.get(f"/notes/{response.json()["id"]}").json()


@pytest.mark.usefixtures("amy")
def test_an_idempotent_create_stays_on_the_orm(client: TestClient) -> None:
    headers = {**bearer(client, "amy"), "Idempotency-Key": "k-1"}
    with statements() as executed:
        first = client.post("/notes", json={"title": "a"}, headers=headers)
        second = client.post("/notes", json={"title": "a"}, headers=headers)
    assert first.status_code == 201, first.text
    assert (second.status_code, second.content) == (201, first.content)
    assert executed["native"] == []
    assert Note.objects.count() == 1
    assert first.json() == client.get(f"/notes/{first.json()["id"]}").json()
    taken = client.post("/notes", json={"title": "a"}, headers={**headers, "Idempotency-Key": "k-2"})
    assert (taken.status_code, taken.json()["code"]) == (409, "conflict")  # 键的事务回滚, 可以重试
    assert not IdempotencyKey.objects.filter(key="k-2").exists()
