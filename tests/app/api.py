import uuid
from typing import TypedDict, override

from freeman.auth import AllowAny, IsAuthenticated
lazy from django.db.models import QuerySet
lazy from freeman import Request

from railguns.rest_framework.actions import actor, run
from railguns.rest_framework.api import API
from railguns.rest_framework.auth import access_auth
from railguns.rest_framework.generics import CreateAPI, ListAPI, ListCreateAPI, RetrieveAPI, RetrieveUpdateAPI
from railguns.rest_framework.pagination import Pagination
from railguns.rest_framework.permissions import BlacklistPermission, IsOwnerOnList, IsOwnerOrReadOnly
from railguns.urls import api as railguns_api

from . import services
from .models import Article, Blacklist, Note, Post
from .serializers import (
    ArticleInput,
    ArticleSerializer,
    Done,
    Me,
    NoteInput,
    NoteSerializer,
    PostInput,
    PostSerializer,
    Publish,
    Published,
    Stamped,
    TitlePage,
)


class Access(TypedDict):
    """注册路由的认证和权限."""

    auth: list[object]
    guards: list[object]


api = API()
AUTH: list[object] = [access_auth]
PUBLIC: Access = {"auth": AUTH, "guards": [AllowAny()]}
PRIVATE: Access = {"auth": AUTH, "guards": [IsAuthenticated()]}


# 资源接口
@api.viewset("/articles", **PUBLIC, tags=["articles"])
class ArticleList(ListCreateAPI):
    """文章列表和创建."""

    model = Article
    serializer_class = ArticleSerializer
    input_class = ArticleInput
    filterset_fields = ("score", "username")


@api.viewset("/articles", **PUBLIC, tags=["articles"])
class ArticleDetail(RetrieveUpdateAPI):
    """文章详情和修改, 只有所有者能改."""

    model = Article
    serializer_class = ArticleSerializer
    input_class = ArticleInput
    object_permissions = (IsOwnerOrReadOnly(),)


@api.viewset("/readonly/articles", **PUBLIC)
class ReadOnlyArticleList(ListAPI):
    """只读的文章列表, 按 score 排序."""

    model = Article
    serializer_class = ArticleSerializer
    ordering = ("score",)


@api.viewset("/readonly/articles", **PUBLIC)
class ReadOnlyArticleDetail(RetrieveAPI):
    """只读的文章详情."""

    model = Article
    serializer_class = ArticleSerializer


@api.viewset("/drafts", **PUBLIC)
class DraftCreate(CreateAPI):
    """只能创建."""

    model = Article
    serializer_class = ArticleSerializer
    input_class = ArticleInput


@api.viewset("/notes", **PUBLIC)
class NoteList(ListCreateAPI):
    """笔记列表和创建."""

    model = Note
    serializer_class = NoteSerializer
    input_class = NoteInput


@api.viewset("/notes", **PUBLIC)
class NoteDetail(RetrieveUpdateAPI):
    """笔记详情和修改."""

    model = Note
    serializer_class = NoteSerializer
    input_class = NoteInput


@api.viewset("/users/{user_id}/articles", **PRIVATE)
class UserArticleList(ListAPI):
    """某个用户的文章, 只有本人能看."""

    model = Article
    serializer_class = ArticleSerializer
    lookup_field = "user_id"
    request_permissions = (IsOwnerOnList(),)


@api.viewset("/guarded/articles", **PUBLIC)
class GuardedArticleList(ListAPI):
    """黑名单里的 IP 不能访问."""

    model = Article
    serializer_class = ArticleSerializer
    request_permissions = (BlacklistPermission(Blacklist),)


@api.viewset("/broken/articles", **PUBLIC)
class BrokenArticleList(ListAPI):
    """筛选时出错, 用来验证资源接口的异常也记日志."""

    model = Article
    serializer_class = ArticleSerializer

    @override
    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        msg = "resource view failed"
        raise RuntimeError(msg)


@api.viewset("/posts", **PUBLIC, tags=["posts"])
class PostList(ListCreateAPI):
    """帖子列表和创建."""

    model = Post
    serializer_class = PostSerializer
    input_class = PostInput


@api.viewset("/kinds/{kind}/posts", **PUBLIC, tags=["posts"])
class KindPostList(ListAPI):
    """路径参数 kind 是有 choices 的字段: 只能是其中的值."""

    model = Post
    serializer_class = PostSerializer


# 业务接口
def publish(request: Request, pk: int, data: Publish) -> Published:
    return run(services.publish, actor(request), pk, data)


def whoami(request: Request) -> Me:
    return run(services.whoami, actor(request))


def stamp(title: str) -> str:
    """Run 之后的处理, 比如签发令牌. 标题是 explode 时在这里出错, 用来验证业务函数的写入也会回滚.

    Returns:
        随机的戳.

    Raises:
        RuntimeError: 标题是 explode.

    """
    if title == "explode":
        msg = "after the service"
        raise RuntimeError(msg)
    return uuid.uuid4().hex


def publish_stamped(request: Request, pk: int, data: Publish) -> Stamped:
    published = run(services.publish, actor(request), pk, data)
    return Stamped(**published.model_dump(), stamp=stamp(data.title))


def titles(request: Request) -> TitlePage:
    pagination = Pagination.of(request)
    count, rows = run(services.titles, actor(request), pagination.offset, pagination.size)
    return TitlePage.model_validate(pagination.page(count, rows))


def check_article(request: Request, pk: int) -> Done:
    return run(services.check_article, actor(request), pk)


def upstream(request: Request, status: int) -> Done:
    return run(services.upstream, actor(request), status)


api.post("/articles/{pk}/publish", idempotent=True, **PRIVATE)(publish)
api.post("/articles/{pk}/stamp", idempotent=True, **PRIVATE)(publish_stamped)
api.get("/whoami", **PUBLIC)(whoami)
api.get("/titles", **PUBLIC)(titles)
api.post("/articles/{pk}/check", **PUBLIC)(check_article)
api.get("/upstream/{status}", **PUBLIC)(upstream)

api.mount("/api/v1", railguns_api)
