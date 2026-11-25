lazy from collections.abc import Iterable

from django.db import models
lazy from django.db.models.base import ModelBase

from railguns.django.db.models import BaseModel, PostModel


class Article(PostModel):
    """内容类模型: 带 is_active, 时间, 所有者三个字段, 标题, 图片, 标签."""

    score = models.IntegerField(default=0)

    class Meta(PostModel.Meta):
        """和 PostModel 一样."""


class Blacklist(models.Model):
    """不能访问的 IP."""

    ip_addr = models.GenericIPAddressField(unique=True)

    def __str__(self) -> str:
        """后台里显示的名字.

        Returns:
            IP 地址.

        """
        return str(self.ip_addr)


class Post(BaseModel):
    """kind 有 choices, 做路径参数. 分类用 id 列引用, 不用外键; id 不能是负数 (数据库里的检查约束)."""

    KINDS = (("news", "新闻"), ("note", "笔记"))
    title = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=KINDS, default="news")
    category_id = models.PositiveBigIntegerField()


class Note(BaseModel):
    """所有者只有 user_id: 创建时直接用令牌里的 id, 不查用户. rank 由数据库生成."""

    user_id = models.PositiveIntegerField(editable=False)
    title = models.CharField(max_length=100, unique=True)
    rank = models.IntegerField(db_default=7)


class LoudArticle(Article):
    """覆盖了 save() 的模型 (代理, 和 Article 同一张表): 创建要走 ORM."""

    class Meta(Article.Meta):
        """代理."""

        proxy = True

    def save(
        self,
        *,
        force_insert: bool | tuple[ModelBase, ...] = False,
        force_update: bool = False,
        using: str | None = None,
        update_fields: Iterable[str] | None = None,
    ) -> None:
        self.summary = "saved"
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
