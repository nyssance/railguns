"""登出: 这一次登录, 所有设备."""

import pytest
lazy from freeman.testing import TestClient

from .base import login, user

pytestmark = pytest.mark.usefixtures("users")


@pytest.fixture
def users(client: TestClient) -> None:
    """建用户 amy 和 bob."""
    user("amy")
    user("bob")


def headers(tokens: dict) -> dict:
    """访问令牌的请求头.

    Returns:
        带 Authorization 的请求头.

    """
    return {"Authorization": f"Bearer {tokens["access"]}"}


def test_logout_ends_this_login_only(client: TestClient) -> None:
    phone, laptop = login(client, "amy"), login(client, "amy")
    response = client.post("/api/v1/auth/logout", json={"refresh": phone["refresh"]}, headers=headers(phone))
    assert (response.status_code, response.json()) == (200, {"ok": True})
    # 这一次登录的访问令牌和刷新令牌都失效
    assert client.get("/users/1/articles", headers=headers(phone)).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh": phone["refresh"]}).status_code == 401
    # 另一台设备上的登录不受影响
    assert client.post("/api/v1/auth/refresh", json={"refresh": laptop["refresh"]}).status_code == 200


def test_logout_needs_the_access_token_and_a_refresh_token_of_the_same_user(client: TestClient) -> None:
    amy, bob = login(client, "amy"), login(client, "bob")
    assert client.post("/api/v1/auth/logout", json={"refresh": amy["refresh"]}).status_code == 401
    mixed = client.post("/api/v1/auth/logout", json={"refresh": bob["refresh"]}, headers=headers(amy))
    assert mixed.status_code == 401
    garbage = client.post("/api/v1/auth/logout", json={"refresh": "nope"}, headers=headers(amy))
    assert garbage.status_code == 401
    # 都没有登出成功
    assert client.post("/api/v1/auth/refresh", json={"refresh": bob["refresh"]}).status_code == 200


def test_logout_all_ends_every_login_of_the_user(client: TestClient) -> None:
    phone, laptop, bob = login(client, "amy"), login(client, "amy"), login(client, "bob")
    response = client.post("/api/v1/auth/logout-all", headers=headers(phone))
    assert (response.status_code, response.json()) == (200, {"ok": True})
    for tokens in (phone, laptop):
        assert client.post("/api/v1/auth/refresh", json={"refresh": tokens["refresh"]}).status_code == 401
    # 发起登出的这台设备, 访问令牌立刻失效
    assert client.get("/whoami", headers=headers(phone)).json().get("user_id") is None
    # 另一台设备的访问令牌活到自己过期 (最长 5 分钟), 但它已经不能续期
    assert client.get("/whoami", headers=headers(laptop)).json().get("user_id") is not None
    # 别的用户不受影响, 自己也能重新登录
    assert client.post("/api/v1/auth/refresh", json={"refresh": bob["refresh"]}).status_code == 200
    login(client, "amy")
