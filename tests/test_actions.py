"""业务动作: 服务的结果, 业务错误, 回滚, 日志."""

import logging
lazy from collections.abc import Iterator

import pytest
lazy from freeman.testing import TestClient
lazy from httpx import Response

from .app.models import Article
from .base import bearer, user


class Capture(logging.Handler):
    """收集日志记录."""

    def __init__(self) -> None:
        """开始时没有记录."""
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@pytest.fixture
def log() -> Iterator[Capture]:
    """收集 django.request 的日志.

    Yields:
        收集到的日志.

    """
    capture = Capture()
    logging.getLogger("django.request").addHandler(capture)
    yield capture
    logging.getLogger("django.request").removeHandler(capture)


@pytest.fixture
def article(client: TestClient) -> Article:
    """用户 amy 的草稿, 另有用户 bob 和员工 staff.

    Returns:
        草稿.

    """
    amy = user("amy")
    user("bob")
    user("staff", is_staff=True)
    return Article.objects.create(user_id=amy.pk, username="amy", title="draft")


def publish(client: TestClient, article: Article, username: str, title: str, url: str | None = None) -> Response:
    """发布文章.

    Returns:
        发布接口的响应.

    """
    return client.post(
        url or f"/articles/{article.pk}/publish", json={"title": title}, headers=bearer(client, username)
    )


def test_service_result_is_returned(client: TestClient, article: Article) -> None:
    response = publish(client, article, "amy", "live")
    assert (response.status_code, response.json()) == (200, {"id": article.pk, "title": "live"})


def test_actor_user_is_loaded_from_the_database(client: TestClient, article: Article) -> None:
    """是否员工不从令牌里读: 员工能改别人的文章, 普通用户不能."""
    assert publish(client, article, "staff", "by staff").status_code == 200
    assert publish(client, article, "bob", "by bob").status_code == 403


def test_business_errors_have_a_code(client: TestClient, article: Article) -> None:
    assert publish(client, article, "bob", "x").json() == {"code": "permission_denied", "detail": "不是你的文章"}
    response = publish(client, article, "amy", "x", "/articles/99999/publish")
    assert (response.status_code, response.json()) == (404, {"code": "not_found", "detail": "没有这篇文章"})
    response = publish(client, article, "amy", "dup")
    assert (response.status_code, response.json()) == (409, {"code": "published", "detail": "已经发布过"})


@pytest.mark.parametrize("title", ["dup", "boom"])
def test_failed_service_is_rolled_back(client: TestClient, article: Article, title: str) -> None:
    publish(client, article, "amy", title)
    article.refresh_from_db()
    assert article.title == "draft"


def test_unexpected_error_is_logged_for_alerting(client: TestClient, article: Article, log: Capture) -> None:
    assert publish(client, article, "amy", "boom").status_code == 500
    errors = [record for record in log.records if record.exc_info]
    assert len(errors) == 1
    assert errors[0].status_code == 500


def test_business_errors_are_not_logged(client: TestClient, article: Article, log: Capture) -> None:
    publish(client, article, "bob", "x")
    assert [record for record in log.records if record.exc_info] == []


def test_actor_user_and_anonymous_actor(client: TestClient, article: Article) -> None:
    assert client.get("/whoami").json() == {"user_id": None, "username": ""}
    assert client.get("/whoami", headers=bearer(client, "amy")).json() == {
        "user_id": article.user_id,
        "username": "amy",
    }


@pytest.mark.usefixtures("article")
def test_resource_view_errors_are_logged_too(client: TestClient, log: Capture) -> None:
    assert client.get("/articles").status_code == 200
    assert log.records == []
    assert client.get("/broken/articles").status_code == 500
    assert len([record for record in log.records if record.exc_info]) == 1
