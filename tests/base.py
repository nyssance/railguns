"""测试的公共函数: 建用户, 登录, 拿 Bearer 头."""

from typing import TypedDict, Unpack

from django.contrib.auth.models import User
lazy from freeman.testing import TestClient

PASSWORD = "pw-123456"


class Flags(TypedDict, total=False):
    """测试用户可以改的标志."""

    is_active: bool
    is_staff: bool


def user(username: str, **fields: Unpack[Flags]) -> User:
    """建一个用户, 密码是 PASSWORD.

    Returns:
        新建的用户.

    """
    return User.objects.create_user(username, password=PASSWORD, **fields)


def login(client: TestClient, username: str) -> dict:
    """用 PASSWORD 登录.

    Returns:
        登录接口返回的数据.

    """
    response = client.post("/api/v1/auth/login", json={"username": username, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()


def bearer(client: TestClient, username: str) -> dict:
    """登录拿访问令牌.

    Returns:
        带 Authorization 的请求头.

    """
    return {"Authorization": f"Bearer {login(client, username)["access"]}"}
