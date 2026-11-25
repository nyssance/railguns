"""登录和刷新令牌."""

import pytest
from django.contrib.auth import get_user_model
lazy from freeman.testing import TestClient
lazy from httpx import Response

from .base import PASSWORD, bearer, login, user

LOGIN, REFRESH = "/api/v1/auth/login", "/api/v1/auth/refresh"


@pytest.fixture
def users(client: TestClient) -> None:
    """建用户 amy 和停用的 off."""
    user("amy")
    user("off", is_active=False)


# 登录


@pytest.mark.usefixtures("users")
def test_returns_tokens_and_profile(client: TestClient) -> None:
    data = login(client, "amy")
    assert sorted(data) == ["access", "refresh", "token", "username"]
    assert data["username"] == "amy"  # 来自 RAILGUNS_LOGIN_PROFILE


@pytest.mark.usefixtures("users")
def test_wrong_password(client: TestClient) -> None:
    response = client.post(LOGIN, json={"username": "amy", "password": "wrong"})
    assert response.status_code == 401


@pytest.mark.usefixtures("users")
def test_inactive_user(client: TestClient) -> None:
    response = client.post(LOGIN, json={"username": "off", "password": PASSWORD})
    assert response.status_code == 401


@pytest.mark.usefixtures("users")
def test_missing_field(client: TestClient) -> None:
    assert client.post(LOGIN, json={"username": "amy"}).status_code == 422


@pytest.mark.usefixtures("users")
def test_access_token_authenticates(client: TestClient) -> None:
    response = client.get("/whoami", headers=bearer(client, "amy"))
    assert response.json()["username"] == "amy"


@pytest.mark.usefixtures("users")
def test_refresh_token_is_not_an_access_token(client: TestClient) -> None:
    headers = {"Authorization": f"Bearer {login(client, "amy")["refresh"]}"}
    assert client.post("/articles/1/publish", json={"title": "x"}, headers=headers).status_code == 401


@pytest.fixture
def pair(client: TestClient) -> dict:
    """用户 amy 登录拿到的一对令牌.

    Returns:
    登录接口返回的数据.

    """
    user("amy")
    return login(client, "amy")


def refresh(client: TestClient, token: str) -> Response:
    """用刷新令牌换一对新的.

    Returns:
    刷新接口的响应.

    """
    return client.post(REFRESH, json={"refresh": token})


# 刷新


def test_issues_a_new_pair(client: TestClient, pair: dict) -> None:
    response = refresh(client, pair["refresh"])
    assert response.status_code == 200
    assert sorted(response.json()) == ["access", "refresh"]
    assert response.json()["refresh"] != pair["refresh"]


def test_access_token_cannot_refresh(client: TestClient, pair: dict) -> None:
    assert refresh(client, pair["access"]).status_code == 401


@pytest.mark.usefixtures("pair")
def test_garbage(client: TestClient) -> None:
    assert refresh(client, "not-a-token").status_code == 401


def test_reuse_revokes_the_whole_family(client: TestClient, pair: dict) -> None:
    """旧的刷新令牌被再次使用说明可能被盗, 这一串令牌全部作废."""
    new = refresh(client, pair["refresh"]).json()
    assert refresh(client, pair["refresh"]).status_code == 401
    assert refresh(client, new["refresh"]).status_code == 401


def test_deactivated_user_cannot_refresh(client: TestClient, pair: dict) -> None:
    get_user_model().objects.filter(username="amy").update(is_active=False)
    assert refresh(client, pair["refresh"]).status_code == 401
