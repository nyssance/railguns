lazy from datetime import datetime

from pydantic import BaseModel, computed_field

from railguns.rest_framework.mixins import ImagesFieldMixin, TagsFieldMixin
from railguns.rest_framework.pagination import Page
lazy from railguns.rest_framework.serializers import ImageList


class ArticleSerializer(BaseModel):
    """响应."""

    id: int
    created_time: datetime
    title: str
    summary: str
    images: str
    tags: str
    score: int
    is_active: bool
    user_id: int
    username: str

    @computed_field
    @property
    def image_list(self) -> ImageList:
        return ImagesFieldMixin().get_images(self)

    @computed_field
    @property
    def tag_list(self) -> list[str]:
        return TagsFieldMixin().get_tags(self)


class ArticleInput(BaseModel):
    """请求体. 这里没有的字段, 请求体改不了."""

    title: str
    summary: str = ""
    images: str = ""
    tags: str = ""
    score: int = 0
    is_active: bool = True


class Publish(BaseModel):
    """发布的请求体."""

    title: str


class Published(BaseModel):
    """发布的结果."""

    id: int
    title: str


class Profile(BaseModel):
    """登录时附带的用户资料 (RAILGUNS_LOGIN_PROFILE)."""

    username: str


class Me(BaseModel):
    """当前用户."""

    user_id: int | None
    username: str


class PostSerializer(BaseModel):
    """帖子的响应."""

    id: int
    title: str
    kind: str
    category_id: int


class PostInput(BaseModel):
    """帖子的请求体."""

    title: str
    category_id: int


class Stamped(BaseModel):
    """发布之后再由处理函数加上的戳: 幂等的接口存下的是处理函数最后的响应."""

    id: int
    title: str
    stamp: str


class Title(BaseModel):
    """一行标题."""

    id: int
    title: str


class TitlePage(Page[Title]):
    """业务接口自己分页."""


class Done(BaseModel):
    """完成."""

    ok: bool


class NoteSerializer(BaseModel):
    """只有列: 创建的响应直接由 INSERT ... RETURNING 建出."""

    id: int
    created_time: datetime
    updated_time: datetime
    title: str
    rank: int
    is_active: bool
    user_id: int


class NoteInput(BaseModel):
    """笔记的请求体."""

    title: str
