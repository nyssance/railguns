"""编译好的读查询的复用 (generics.STATEMENTS) 和一页的直接编码."""

from types import SimpleNamespace
from typing import cast
lazy from datetime import datetime

import pytest
from django_filters import FilterSet
from freeman._pydantic import adapter_for
from freeman.responses import Response
from pydantic import BaseModel, field_validator
lazy from django.contrib.auth.models import AbstractBaseUser
lazy from django.db.models import QuerySet
lazy from freeman.request import Request
lazy from freeman.testing import TestClient

from railguns.rest_framework.generics import API, STATEMENTS, ListAPI, Statements
from railguns.rest_framework.permissions import get_user_id

from .app.api import ArticleList, BrokenArticleList, UserArticleList
from .app.models import Article
from .base import bearer, user


def view(cls: type[API], query: dict | None = None, params: dict | None = None, action: str = "list") -> API:
    """不经过请求, 直接建一个视图.

    Returns:
        视图.

    """
    request = cast("Request", SimpleNamespace(query=query or {}))  # 视图只读 query, 用一个假的请求
    return cls(request, action, params or {})


# 有上限的最近最少使用缓存


def test_the_bound_holds_and_the_least_recently_used_goes_first() -> None:
    cache = Statements(3)
    for index in range(3):
        cache.put((index,), ("default", f"q{index}", ()))
    cache.get((0,))  # 0 刚用过, 最久没用的是 1
    cache.put((3,), ("default", "q3", ()))
    cache.put((4,), ("default", "q4", ()))
    assert len(cache) == 3
    assert [cache.get((index,)) is not None for index in range(5)] == [True, False, False, True, True]


# 缓存的键


def test_a_class_that_overrides_the_queryset_is_never_cached() -> None:
    class Mine(ListAPI):
        model = Article
        serializer_class = BaseModel

        async def get_queryset(self) -> QuerySet:  # 取决于当前用户
            return Article.objects.filter(user_id=get_user_id(self.request))

    assert not Mine.is_pure()
    assert not BrokenArticleList.is_pure()
    assert view(Mine).statement_key(20, 1) is None
    assert view(BrokenArticleList).statement_key(20, 1) is None
    assert ArticleList.is_pure()


def test_every_input_is_in_the_key() -> None:
    keys = {
        view(UserArticleList, params={"user_id": 1}).statement_key(20, 1),
        view(UserArticleList, params={"user_id": 2}).statement_key(20, 1),
        view(UserArticleList, params={"user_id": 1}).statement_key(10, 1),
        view(UserArticleList, params={"user_id": 1}).statement_key(20, 2),
        view(ArticleList, {"score": "1"}).statement_key(20, 1),
        view(ArticleList, {"score": "2"}).statement_key(20, 1),
        view(ArticleList, {"score": "2", "username": "amy"}).statement_key(20, 1),
        view(ArticleList).statement_key(20, 1),
    }
    assert len(keys) == 8
    # 不是筛选参数的查询参数不影响查询, 不进键
    assert view(ArticleList, {"x": "1"}).statement_key(20, 1) == view(ArticleList).statement_key(20, 1)


def test_an_unhashable_input_skips_the_cache() -> None:
    assert view(ArticleList, {"score": ["1", "2"]}).statement_key(20, 1) is None


def test_a_declared_filterset_is_not_cached_when_it_is_used() -> None:
    class Filters(FilterSet):
        class Meta:
            model = Article
            fields = ("score",)

    class Filtered(ListAPI):
        model = Article
        serializer_class = BaseModel
        filterset_class = Filters

    assert view(Filtered, {"score": "1"}).statement_key(20, 1) is None
    assert view(Filtered).statement_key(20, 1) is not None


# 一页的直接编码


class Plain(BaseModel):
    """只有列的响应: 一页可以直接编码."""

    id: int
    created_time: datetime
    title: str
    score: int
    is_active: bool
    username: str


class PlainList(ListAPI):
    """响应只有列的列表."""

    model = Article
    serializer_class = Plain


@pytest.mark.usefixtures("client")
@pytest.mark.parametrize("count", [3, 0])
def test_direct_encoding_gives_the_same_bytes(count: int) -> None:
    amy = user("amy")
    for index in range(3):
        Article.objects.create(user_id=amy.pk, username="amy", title=f"t{index}", score=index)
    names = PlainList.columns()
    assert names == list(Plain.model_fields)  # 列按声明的顺序
    rows = list(Article.objects.order_by("-pk").values(*names))
    page_class = PlainList.page_class()
    page = (
        {"count": count, "next": "http://x/?page=2", "previous": None, "results": rows}
        if count
        else {"count": 0, "next": None, "previous": None, "results": []}
    )
    adapter = adapter_for(page_class)
    expected = adapter.dump_json(adapter.validate_python(page, from_attributes=True))
    response = PlainList.encode_page(page_class, page)
    assert isinstance(response, Response)
    assert response.content == expected


def test_only_a_serializer_of_plain_columns_is_encoded_directly() -> None:
    class Checked(Plain):
        @field_validator("title")
        @classmethod
        def strip(cls, value: str) -> str:
            return value.strip()

    class CheckedList(ListAPI):
        model = Article
        serializer_class = Checked

    assert PlainList.page_encoder(PlainList.page_class()) is not None
    assert PlainList.page_encoder(None) is not None  # 详情的一行
    for cls in (ArticleList, CheckedList):  # ArticleList 有计算字段
        assert cls.page_encoder(cls.page_class()) is None, cls.__name__


# 编译好的语句的复用


@pytest.fixture
def members(client: TestClient) -> tuple[AbstractBaseUser, AbstractBaseUser]:
    """用户 amy 的七篇文章 (第四篇下线) 和用户 bob 的一篇, 缓存是空的.

    Returns:
        amy 和 bob.

    """
    STATEMENTS.clear()
    amy, bob = user("amy"), user("bob")
    for index in range(1, 8):
        Article.objects.create(user_id=amy.pk, username="amy", title=f"a{index}", score=index % 3, is_active=index != 4)
    Article.objects.create(user_id=bob.pk, username="bob", title="b1", score=1)
    return amy, bob


def responses(client: TestClient, urls: list[str]) -> list[tuple[int, str]]:
    """依次请求.

    Returns:
        每个请求的状态码和响应体.

    """
    return [(response.status_code, response.text) for response in map(client.get, urls)]


@pytest.mark.usefixtures("members")
def test_cold_and_warm_give_the_same_responses(client: TestClient) -> None:
    first = Article.objects.get(title="a1").pk
    urls = [
        "/articles",
        "/articles?page_size=3",
        "/articles?page_size=3&page=2",
        "/articles?page_size=3&page=3",
        "/articles?page_size=3&page=4",
        "/articles?page=0",
        "/articles?page=abc",
        "/articles?page_size=0",
        "/articles?page_size=100000",
        "/articles?score=1",
        "/articles?score=1&username=bob",
        "/articles?username=nobody",
        "/articles?score=abc",
        "/articles?score=abc&page=0",
        "/readonly/articles",
        f"/articles/{first}",
        f"/articles/{first + 3}",
        "/articles/99999",
        f"/readonly/articles/{first}",
    ]
    STATEMENTS.clear()
    cold = responses(client, urls)
    assert len(STATEMENTS) > 0
    warm = responses(client, urls)
    assert cold == warm
    assert [status for status, _ in cold].count(404) == 5
    assert [status for status, _ in cold].count(400) == 2


@pytest.mark.usefixtures("members")
def test_an_invalid_filter_is_refused_every_time_and_never_stored(client: TestClient) -> None:
    for _ in range(3):
        assert client.get("/articles?score=abc").status_code == 400
    assert len(STATEMENTS) == 0


def test_path_parameters_never_share_a_statement(
    client: TestClient, members: tuple[AbstractBaseUser, AbstractBaseUser]
) -> None:
    for _ in range(2):  # 第二轮全部命中
        for member in members:
            data = client.get(f"/users/{member.pk}/articles", headers=bearer(client, member.get_username())).json()
            assert {row["username"] for row in data["results"]} == {member.get_username()}
    assert len([key for key in STATEMENTS.entries if key[0] is UserArticleList]) == 2


@pytest.mark.usefixtures("members")
def test_an_overriding_class_is_not_stored(client: TestClient) -> None:
    client.get("/broken/articles")
    assert not [key for key in STATEMENTS.entries if key[0] is BrokenArticleList]


@pytest.mark.usefixtures("members")
def test_a_warm_statement_reads_the_current_rows(client: TestClient) -> None:
    assert client.get("/articles?page_size=3&page=3").status_code == 200
    Article.objects.filter(title__in=["a1", "a2"]).update(is_active=False)
    data = client.get("/articles?page_size=3").json()
    assert data["count"] == 5
    assert client.get("/articles?page_size=3&page=3").status_code == 404
    Article.objects.all().update(is_active=False)
    assert client.get("/articles?page_size=3").json()["count"] == 0
