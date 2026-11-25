"""云存储: 上传参数和下载地址."""

import pytest
from django.conf import settings
from django.test import Client
lazy from django.contrib.auth.models import AbstractBaseUser
lazy from freeman.testing import TestClient

from .base import bearer, user

UPLOAD = "/api/v1/upload-params/aliyun"
DOWNLOAD = "/api/v1/download-url/aliyun"
DOMAIN = settings.CLOUD_STORAGE_DOMAIN_NAME


@pytest.fixture
def staff(client: TestClient) -> AbstractBaseUser:
    """员工 staff, 另有普通用户 amy.

    Returns:
        员工.

    """
    user("amy")
    return user("staff", is_staff=True)


def session(member: AbstractBaseUser) -> dict:
    """后台上传控件的调用方式: 登录后台的会话 Cookie, 不带访问令牌.

    Returns:
        带会话 Cookie 和 Origin 的请求头.

    """
    django = Client()
    django.force_login(member)
    return {
        "Cookie": "; ".join(f"{key}={morsel.value}" for key, morsel in django.cookies.items()),
        "Origin": "http://testserver",
    }


@pytest.mark.usefixtures("staff")
def test_upload_with_access_token(client: TestClient) -> None:
    response = client.post(UPLOAD, json={"filename": "photo.png"}, headers=bearer(client, "amy"))
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["endpoint"] == settings.MEDIA_URL
    assert data["params"]["OSSAccessKeyId"] == settings.CLOUD_STORAGE_ID
    assert data["params"]["key"].endswith(".png")
    assert "photo" not in data["params"]["key"]  # media 桶里的文件会被重命名
    assert all(isinstance(value, str) for value in data["params"].values())


def test_upload_with_admin_session(client: TestClient, staff: AbstractBaseUser) -> None:
    response = client.post(UPLOAD, json={"filename": "a.png"}, headers=session(staff))
    assert response.status_code == 200, response.text


def test_session_from_another_site_is_refused(client: TestClient, staff: AbstractBaseUser) -> None:
    headers = {**session(staff), "Origin": "http://evil.example"}
    assert client.post(UPLOAD, json={"filename": "a.png"}, headers=headers).status_code == 403


@pytest.mark.usefixtures("staff")
def test_no_credentials(client: TestClient) -> None:
    assert client.post(UPLOAD, json={"filename": "a.png"}).status_code == 401
    assert client.get(f"{DOWNLOAD}?url=https://media.{DOMAIN}/a").status_code == 401


@pytest.mark.usefixtures("staff")
def test_only_known_clouds(client: TestClient) -> None:
    response = client.post("/api/v1/upload-params/tencent", json={"filename": "a.png"}, headers=bearer(client, "amy"))
    assert response.status_code == 404


@pytest.mark.usefixtures("staff")
def test_other_buckets_need_staff(client: TestClient) -> None:
    body = {"filename": "a.css", "bucket": settings.BUCKET_STATIC}
    assert client.post(UPLOAD, json=body, headers=bearer(client, "amy")).status_code == 403
    response = client.post(UPLOAD, json=body, headers=bearer(client, "staff"))
    assert response.status_code == 200, response.text
    assert response.json()["params"]["key"] == "a.css"  # static 桶保留原文件名


@pytest.mark.usefixtures("staff")
def test_unknown_bucket_and_missing_filename(client: TestClient) -> None:
    headers = bearer(client, "staff")
    assert client.post(UPLOAD, json={"filename": "a", "bucket": "nope"}, headers=headers).status_code == 400
    assert client.post(UPLOAD, json={"filename": ""}, headers=headers).status_code == 400


@pytest.mark.usefixtures("staff")
def test_download_url_is_signed(client: TestClient) -> None:
    url = f"https://media.{DOMAIN}/contract/a.pdf"
    response = client.get(f"{DOWNLOAD}?url={url}", headers=bearer(client, "amy"))
    assert response.status_code == 200, response.text
    signed = response.json()["url"]
    assert signed.startswith(f"{url}?OSSAccessKeyId={settings.CLOUD_STORAGE_ID}&Expires=")
    assert "&Signature=" in signed


@pytest.mark.usefixtures("staff")
@pytest.mark.parametrize("url", [f"https://other.{DOMAIN}/a", f"http://media.{DOMAIN}/a", "https://evil.example/a", ""])
def test_download_url_only_for_own_buckets(client: TestClient, url: str) -> None:
    assert client.get(f"{DOWNLOAD}?url={url}", headers=bearer(client, "amy")).status_code == 400
