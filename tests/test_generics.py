import pytest
lazy from django.contrib.auth.models import AbstractBaseUser
lazy from freeman.testing import TestClient

from railguns.management.commands.openapi import document
from railguns.testing.matrix import sample_path

from .app.api import KindPostList
from .app.models import Article, Blacklist, Post
from .base import bearer, user

pytestmark = pytest.mark.django_db(transaction=True)


def article(owner: AbstractBaseUser, title: str = "t", **fields: object) -> Article:
    return Article.objects.create(user_id=owner.pk, username=owner.get_username(), title=title, **fields)


@pytest.fixture
def amy() -> AbstractBaseUser:
    return user("amy")


@pytest.fixture
def bob() -> AbstractBaseUser:
    return user("bob")


# 列表


@pytest.fixture
def listed(amy: AbstractBaseUser) -> AbstractBaseUser:
    for index in range(1, 6):
        article(amy, f"a{index}", score=index, is_active=index != 3)
    return amy


@pytest.mark.usefixtures("listed")
def test_envelope_and_inactive_rows_hidden(client: TestClient) -> None:
    data = client.get("/articles").json()
    assert sorted(data) == ["count", "next", "previous", "results"]
    assert data["count"] == 4
    assert "a3" not in [row["title"] for row in data["results"]]


@pytest.mark.usefixtures("listed")
def test_default_order_is_newest_first(client: TestClient) -> None:
    assert [row["title"] for row in client.get("/articles").json()["results"]] == ["a5", "a4", "a2", "a1"]


@pytest.mark.usefixtures("listed")
def test_view_ordering(client: TestClient) -> None:
    titles = [row["title"] for row in client.get("/readonly/articles").json()["results"]]
    assert titles == ["a1", "a2", "a4", "a5"]


@pytest.mark.usefixtures("listed")
def test_page_links(client: TestClient) -> None:
    first = client.get("/articles?page_size=2").json()
    assert (len(first["results"]), first["previous"]) == (2, None)
    assert first["next"].endswith("/articles?page_size=2&page=2")
    second = client.get("/articles?page_size=2&page=2").json()
    assert second["next"] is None
    assert second["previous"].endswith("/articles?page_size=2")


@pytest.mark.usefixtures("listed")
def test_short_last_page(client: TestClient) -> None:
    assert len(client.get("/articles?page_size=3&page=2").json()["results"]) == 1


@pytest.mark.usefixtures("listed")
@pytest.mark.parametrize("page", ["0", "99", "abc", "last"])
def test_invalid_page(client: TestClient, page: str) -> None:
    assert client.get(f"/articles?page={page}").status_code == 404


@pytest.mark.usefixtures("listed")
def test_page_size_is_capped(client: TestClient) -> None:
    assert len(client.get("/articles?page_size=100000").json()["results"]) == 4


@pytest.mark.usefixtures("listed")
def test_filter(client: TestClient) -> None:
    assert client.get("/articles?score=2").json()["count"] == 1
    assert client.get("/articles?username=nobody").json()["count"] == 0
    assert client.get("/articles?score=abc").status_code == 400


def test_computed_fields(client: TestClient, listed: AbstractBaseUser) -> None:
    article(listed, "media", images=" a.png\n\n b.png ", tags="one## two ")
    row = client.get("/articles").json()["results"][0]
    assert row["image_list"] == {"count": 2, "data": [{"uri": "a.png"}, {"uri": "b.png"}]}
    assert row["tag_list"] == ["one", "two"]


# 详情


def test_detail(client: TestClient, amy: AbstractBaseUser) -> None:
    visible = article(amy, "visible")
    assert client.get(f"/articles/{visible.pk}").json()["title"] == "visible"


def test_inactive_and_missing_are_404(client: TestClient, amy: AbstractBaseUser) -> None:
    article(amy, "visible")
    hidden = article(amy, "hidden", is_active=False)
    assert client.get(f"/articles/{hidden.pk}").status_code == 404
    assert client.get("/articles/99999").status_code == 404
    assert client.get(f"/readonly/articles/{hidden.pk}").status_code == 404


# 新建


@pytest.mark.usefixtures("amy")
def test_requires_login(client: TestClient) -> None:
    assert client.post("/articles", json={"title": "x"}).status_code == 401
    assert Article.objects.count() == 0


@pytest.mark.parametrize("path", ["/articles", "/drafts"])
def test_owner_is_taken_from_the_token(client: TestClient, amy: AbstractBaseUser, path: str) -> None:
    response = client.post(path, json={"title": path}, headers=bearer(client, "amy"))
    assert response.status_code in {200, 201}, response.text
    created = Article.objects.get(title=path)
    assert (created.user_id, created.username) == (amy.pk, "amy")


def test_read_only_fields_in_the_body_are_ignored(client: TestClient, amy: AbstractBaseUser) -> None:
    body = {"title": "x", "id": 777, "user_id": 999, "username": "mallory", "created_time": "2000-01-01T00:00:00Z"}
    client.post("/articles", json=body, headers=bearer(client, "amy"))
    created = Article.objects.get(title="x")
    assert created.pk != 777
    assert (created.user_id, created.username) == (amy.pk, "amy")
    assert created.created_time.year > 2000


@pytest.mark.usefixtures("amy")
def test_validation(client: TestClient) -> None:
    assert client.post("/articles", json={}, headers=bearer(client, "amy")).status_code == 422


# 修改


@pytest.fixture
def mine(amy: AbstractBaseUser, bob: AbstractBaseUser) -> Article:
    return article(amy, "mine")


def test_owner_can_patch(client: TestClient, mine: Article) -> None:
    response = client.patch(f"/articles/{mine.pk}", json={"title": "changed"}, headers=bearer(client, "amy"))
    assert response.status_code == 200, response.text
    mine.refresh_from_db()
    assert mine.title == "changed"


def test_other_user_is_refused_but_can_read(client: TestClient, mine: Article) -> None:
    url, headers = f"/articles/{mine.pk}", bearer(client, "bob")
    assert client.patch(url, json={"title": "stolen"}, headers=headers).status_code == 403
    assert client.get(url, headers=headers).status_code == 200
    mine.refresh_from_db()
    assert mine.title == "mine"


def test_anonymous_is_refused(client: TestClient, mine: Article) -> None:
    assert client.patch(f"/articles/{mine.pk}", json={"title": "x"}).status_code in {401, 403}


def test_read_only_fields_cannot_be_changed(
    client: TestClient, mine: Article, amy: AbstractBaseUser, bob: AbstractBaseUser
) -> None:
    body = {"title": "ok", "id": 555, "user_id": bob.pk, "username": "bob"}
    client.patch(f"/articles/{mine.pk}", json=body, headers=bearer(client, "amy"))
    pk = mine.pk
    mine.refresh_from_db()
    assert (mine.pk, mine.user_id, mine.username, mine.title) == (pk, amy.pk, "amy", "ok")
    assert not Article.objects.filter(pk=555).exists()


def test_owner_can_reach_an_inactive_row_for_writing(client: TestClient, mine: Article) -> None:
    url = f"/articles/{mine.pk}"
    Article.objects.filter(pk=mine.pk).update(is_active=False)
    assert client.get(url).status_code == 404
    response = client.patch(url, json={"is_active": True}, headers=bearer(client, "amy"))
    assert response.status_code == 200, response.text


# 请求级权限


@pytest.mark.usefixtures("bob")
def test_owner_list(client: TestClient, amy: AbstractBaseUser) -> None:
    article(amy)
    url = f"/users/{amy.pk}/articles"
    assert client.get(url, headers=bearer(client, "amy")).status_code == 200
    assert client.get(url, headers=bearer(client, "bob")).status_code == 403
    assert client.get(url).status_code == 401


def test_blacklist(client: TestClient, amy: AbstractBaseUser) -> None:
    article(amy)
    assert client.get("/guarded/articles").status_code == 200
    Blacklist.objects.create(ip_addr="127.0.0.1")
    assert client.get("/guarded/articles").status_code == 403


# 路径参数 kind 是有 choices 的字段. 别的表的行用 id 列 (category_id) 引用, 和别的列一样读出.


def test_only_a_choice_is_accepted(client: TestClient) -> None:
    post = Post.objects.create(title="n", category_id=7)
    listed = client.get("/kinds/news/posts").json()
    assert listed["results"] == [{"id": post.pk, "title": "n", "kind": "news", "category_id": 7}]
    assert client.get("/kinds/note/posts").json()["count"] == 0
    response = client.get("/kinds/unknown/posts")
    assert (response.status_code, response.json()["fields"][0]["loc"]) == (422, ["path", "kind"])


def test_documented_as_an_enum_and_sampled() -> None:
    [parameter] = document()["paths"]["/kinds/{kind}/posts"]["get"]["parameters"][:1]
    assert parameter["schema"] == {"type": "string", "enum": ["news", "note"]}
    handler = KindPostList.as_handler("list", "/kinds/{kind}/posts")
    assert sample_path("/kinds/{kind}/posts/{pk}", handler) == "/kinds/news/posts/1"
