"""写死的约定: 数据库, 输入模型, 错误格式."""

import re
from contextlib import contextmanager
lazy from collections.abc import Generator

import pytest
from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.core.checks import run_checks
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import override_settings
from django.test.utils import isolate_apps
from pydantic import BaseModel
lazy from django.apps.registry import Apps
lazy from freeman.testing import TestClient
lazy from pytest_django import Settings

from railguns.checks import (
    errors_for,
    foreign_key_apps,
    foreign_key_apps_setting,
    is_project_app,
    relation_errors,
    relations,
)
from railguns.rest_framework.api import API
from railguns.rest_framework.generics import ListAPI, ListCreateAPI, RetrieveUpdateAPI
lazy from railguns.rest_framework import generics

from .app.models import Article, Post
from .app.serializers import ArticleInput, ArticleSerializer, PostSerializer
from .base import bearer, user

POSTGRES = {"ENGINE": "django.db.backends.postgresql", "OPTIONS": {"pool": True}}


class Brief(BaseModel):
    """嵌套在资源里的模型: 不是列."""

    id: int
    name: str


# 数据库


@pytest.mark.parametrize("engine", ["django.db.backends.sqlite3", "django.db.backends.mysql"])
def test_only_postgresql(engine: str) -> None:
    [error] = errors_for({"default": {"ENGINE": engine}})
    assert error.id == "railguns.E001"


def test_a_pool_is_required() -> None:
    [error] = errors_for({"default": {"ENGINE": "django.db.backends.postgresql"}})
    assert error.id == "railguns.E002"
    assert errors_for({"default": POSTGRES, "replica": POSTGRES}) == []


def test_every_database_is_checked() -> None:
    errors = errors_for({"default": POSTGRES, "replica": {"ENGINE": "django.db.backends.postgresql"}})
    assert [error.id for error in errors] == ["railguns.E002"]


def test_the_project_passes() -> None:
    assert [message for message in run_checks() if message.id and message.id.startswith("railguns.")] == []


# railguns.E003: 项目的模型不用外键. 模型定义在隔离的注册表里, 不建表.


@contextmanager
def isolated(*installed_apps: str) -> Generator[Apps]:
    """isolate_apps 的上下文管理器形式, 产出隔离的注册表.

    Yields:
        隔离的注册表.

    """
    with isolate_apps(*installed_apps) as registry:
        assert registry is not None  # 不传 attr_name / kwarg_name 时 enable() 返回注册表, 存根写成了 Apps | None
        yield registry


def test_every_relation_is_reported() -> None:
    with isolated("tests.app") as registry:

        class Category(models.Model):
            name = models.CharField(max_length=50)

            class Meta:
                app_label = "app"

        class Tagged(models.Model):
            category = models.ForeignKey(Category, on_delete=models.CASCADE)
            profile = models.OneToOneField(Category, on_delete=models.CASCADE, related_name="+")
            tags = models.ManyToManyField(Category, related_name="+")
            owner_id = models.BigIntegerField()  # 普通的 id 列: 不报

            class Meta:
                app_label = "app"

        class Child(Category):  # 多表继承: 自动加的 category_ptr 是一对一
            class Meta:
                app_label = "app"

        errors = relations([registry.get_app_config("app")])
        assert {(error.id, error.obj, error.msg.split(" 是 ")[0]) for error in errors} == {
            ("railguns.E003", Tagged, "app.Tagged.category"),
            ("railguns.E003", Tagged, "app.Tagged.profile"),
            ("railguns.E003", Tagged, "app.Tagged.tags"),
            ("railguns.E003", Child, "app.Child.category_ptr"),
        }
        messages = {error.msg for error in errors}
        assert "app.Tagged.category 是 ForeignKey. 模型之间不用外键, 资源只输出列和计算字段." in messages
        assert "app.Tagged.profile 是 OneToOneField. 模型之间不用外键, 资源只输出列和计算字段." in messages
        assert "app.Tagged.tags 是 ManyToManyField. 模型之间不用外键, 资源只输出列和计算字段." in messages
        assert relation_errors([Category]) == []


def test_fields_declared_by_django_are_not_reported() -> None:
    """AbstractUser (PermissionsMixin) 声明的 groups, user_permissions 不报; 项目自己声明的外键照报."""
    with isolated("tests.app") as registry:

        class Team(models.Model):
            class Meta:
                app_label = "app"

        class Member(AbstractUser):
            team = models.ForeignKey(Team, on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        class Owned(models.Model):  # 项目的抽象基类声明的外键, 报在具体的子模型上
            team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="+")

            class Meta:
                abstract = True

        class Ticket(Owned):
            class Meta:
                app_label = "app"

        errors = relations([registry.get_app_config("app")])
        assert sorted((error.obj.__name__, error.msg.split(" 是 ")[0]) for error in errors) == [
            ("Member", "app.Member.team"),
            ("Ticket", "app.Ticket.team"),
        ]


def test_apps_allowed_to_use_foreign_keys() -> None:
    """RAILGUNS_FOREIGN_KEY_APPS 里的应用整个不查; 别的应用里指向它的外键照报."""
    with isolated("tests.app", "railguns") as registry:

        class Plan(models.Model):
            parent = models.ForeignKey("self", on_delete=models.CASCADE)

            class Meta:
                app_label = "app"

        class Usage(models.Model):
            plan = models.ForeignKey(Plan, on_delete=models.CASCADE)

            class Meta:
                app_label = "railguns"

        configs = [registry.get_app_config("app"), registry.get_app_config("railguns")]
        assert {error.msg.split(" 是 ")[0] for error in relations(configs)} == {
            "app.Plan.parent",
            "railguns.Usage.plan",
        }
        with override_settings(RAILGUNS_FOREIGN_KEY_APPS=["app"]):
            assert foreign_key_apps_setting(None) == []
            assert [error.msg.split(" 是 ")[0] for error in relations(configs)] == ["railguns.Usage.plan"]
        with override_settings(RAILGUNS_FOREIGN_KEY_APPS=("app", "railguns")):
            assert relations(configs) == []


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (["app", "architekt"], "没有安装: ['architekt']"),
        ("app", "必须是应用标签"),
        (["app", 1], "必须是应用标签"),
        ({"app": True}, "必须是应用标签"),
    ],
)
def test_the_foreign_key_apps_setting_is_validated(settings: Settings, value: object, message: str) -> None:
    """写错 (没有安装的应用, 不是字符串列表) 报 E004, 并且不放过任何应用."""
    settings.RAILGUNS_FOREIGN_KEY_APPS = value
    [error] = foreign_key_apps_setting(None)
    assert error.id == "railguns.E004"
    assert message in error.msg
    assert foreign_key_apps()[0] == set()
    assert "railguns.E004" in [message.id for message in run_checks()]


def test_only_project_apps_are_checked() -> None:
    checked = {config.name: is_project_app(config) for config in apps.get_app_configs()}
    assert checked == {
        "django.contrib.admin": False,
        "django.contrib.auth": False,
        "django.contrib.contenttypes": False,
        "django.contrib.sessions": False,
        "django.contrib.messages": False,
        "django.contrib.staticfiles": False,
        "django_ckeditor_5": False,
        "freeman": False,
        "railguns": True,
        "tests.app": True,
    }
    assert relations(None) == []  # 项目 (railguns 和 tests.app) 的模型都没有外键
    # django.contrib.auth 有外键和多对多 (Permission.content_type, User.groups), 不是项目的, 不报
    assert relations([apps.get_app_config("auth")]) == []


# 资源类的声明, 启动时检查


def register(view: type[generics.API]) -> None:
    API().viewset("/things")(view)


def refused(fields: dict, message: str) -> None:
    serializer = type("Shape", (BaseModel,), {"__annotations__": fields})
    with pytest.raises(ImproperlyConfigured, match=re.escape(message)):
        register(type("Things", (ListAPI,), {"model": Post, "serializer_class": serializer}))


def test_write_needs_an_input_class() -> None:
    class Things(ListCreateAPI):
        model = Article
        serializer_class = ArticleSerializer

    with pytest.raises(ImproperlyConfigured, match="必须声明 input_class"):
        register(Things)


@pytest.mark.parametrize("name", ["id", "user_id", "username"])
def test_input_cannot_hold_the_key_or_the_owner(name: str) -> None:
    fields = {"__annotations__": {"title": str, name: int}}

    class Things(RetrieveUpdateAPI):
        model = Article
        serializer_class = ArticleSerializer
        input_class = type("Input", (BaseModel,), fields)

    with pytest.raises(ImproperlyConfigured, match="不能有主键和所有者字段"):
        register(Things)


def test_input_fields_must_be_model_fields() -> None:
    class Input(BaseModel):
        title: str
        nickname: str = ""

    class Things(RetrieveUpdateAPI):
        model = Article
        serializer_class = ArticleSerializer
        input_class = Input

    with pytest.raises(ImproperlyConfigured, match="不是 Article 的字段"):
        register(Things)


def test_serializer_must_be_pydantic() -> None:
    class Things(ListAPI):
        model = Article
        serializer_class = dict

    with pytest.raises(ImproperlyConfigured, match="必须是 Pydantic 模型"):
        register(Things)


def test_a_field_must_be_a_column() -> None:
    refused({"id": int, "nickname": str}, "nickname 不是 Post 的列. 字段只能是列, 或者计算字段")
    refused({"id": int, "pk": int}, "pk 不是 Post 的列")  # 模型上的属性也不行: 列表读不到它


@pytest.mark.parametrize(
    "fields",
    [{"id": int, "category": Brief}, {"id": int, "category": Brief | None}, {"id": int, "comments": list[Brief]}],
)
def test_a_nested_model_is_not_a_column(fields: dict) -> None:
    """模型之间不用外键: 类型是 Pydantic 模型或 list[Model] 的字段不是列, 启动报错."""
    refused(fields, "的类型是 Pydantic 模型, 它不是 Post 的列. 模型之间不用外键")


def test_columns_and_computed_fields_pass() -> None:
    class Things(ListAPI):
        model = Post
        serializer_class = PostSerializer

    register(Things)
    register(type("More", (ListAPI,), {"model": Article, "serializer_class": ArticleSerializer}))


def test_a_read_only_class_needs_no_input_class() -> None:
    class Things(ListAPI):
        model = Article
        serializer_class = ArticleSerializer

    register(Things)


def test_the_error_format_is_fixed() -> None:
    with pytest.raises(TypeError, match="错误格式是固定的"):
        API(error_formatter=lambda *_: None)


def test_partial_input_keeps_the_fields_and_makes_them_optional() -> None:
    class Things(RetrieveUpdateAPI):
        model = Article
        serializer_class = ArticleSerializer
        input_class = ArticleInput

    partial = Things.partial_input()
    assert set(partial.model_fields) == set(ArticleInput.model_fields)
    assert partial().model_dump(exclude_unset=True) == {}
    assert partial(title="x").model_dump(exclude_unset=True) == {"title": "x"}


# 每一层的错误都是 {"code", "detail"}, 字段错误再加 "fields".


def test_refused_by_the_guard(client: TestClient) -> None:
    response = client.post("/articles", json={"title": "x"})
    assert response.status_code == 401
    assert set(response.json()) == {"code", "detail"}
    assert response.json()["code"] == "not_authenticated"


def test_no_route(client: TestClient) -> None:
    response = client.get("/nowhere")
    assert (response.status_code, response.json()["code"]) == (404, "not_found")


def test_a_path_parameter_of_the_wrong_type(client: TestClient) -> None:
    response = client.get("/articles/abc")
    assert response.status_code == 422
    assert response.json()["fields"][0]["loc"] == ["path", "pk"]


def test_a_body_that_does_not_validate_lists_every_field(client: TestClient) -> None:
    user("amy")
    response = client.post("/articles", json={"score": "many", "is_active": "maybe"}, headers=bearer(client, "amy"))
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "validation"
    assert {tuple(field["loc"]) for field in data["fields"]} == {
        ("body", "title"),
        ("body", "score"),
        ("body", "is_active"),
    }


def test_a_missing_object(client: TestClient) -> None:
    response = client.get("/articles/99999")
    assert response.status_code == 404
    assert set(response.json()) == {"code", "detail"}


def test_a_business_error_names_its_code(client: TestClient) -> None:
    amy = user("amy")
    article = Article.objects.create(user_id=amy.pk, username="amy", title="t")
    response = client.post(f"/articles/{article.pk}/publish", json={"title": "dup"}, headers=bearer(client, "amy"))
    assert response.status_code == 409
    assert response.json() == {"code": "published", "detail": "已经发布过"}


def test_an_unhandled_error_does_not_leak(client: TestClient) -> None:
    response = client.get("/broken/articles")
    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "resource view failed" not in response.text


# 写的响应


def test_create_answers_201_with_the_object(client: TestClient) -> None:
    user("amy")
    response = client.post("/articles", json={"title": "new", "tags": "a#b"}, headers=bearer(client, "amy"))
    assert response.status_code == 201, response.text
    data = response.json()
    assert (data["title"], data["username"], data["tag_list"]) == ("new", "amy", ["a", "b"])
    assert data["created_time"]


def test_put_replaces_every_writable_field(client: TestClient) -> None:
    amy = user("amy")
    article = Article.objects.create(user_id=amy.pk, username="amy", title="old", summary="keep?", score=5)
    response = client.put(f"/articles/{article.pk}", json={"title": "new"}, headers=bearer(client, "amy"))
    assert response.status_code == 200, response.text
    article.refresh_from_db()
    assert (article.title, article.summary, article.score) == ("new", "", 0)
