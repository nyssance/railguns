from typing import Any, ClassVar, Self

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from railguns.django.utils.translation import dj_gettext
from railguns.django.utils.translation import format_gettext_lazy as _f

from .utils import db_master, generate_shard_id, get_user_id


class DateTimeModelMixin(models.Model):
    """创建时间和更新时间."""

    created_time = models.DateTimeField(_("created_time"), auto_now_add=True)
    updated_time = models.DateTimeField(_("updated_time"), auto_now=True)

    class Meta:
        """模型的元数据."""

        abstract = True


class AbstractBaseModel(DateTimeModelMixin):
    """模型的基类: 时间, 是否有效, 默认按主键倒序."""

    is_active = models.BooleanField(dj_gettext("active"), default=True)

    # 只是为了PyLint不警告, SO https://stackoverflow.com/questions/45135263/class-has-no-objects-member#45150811
    objects: ClassVar[models.Manager[Self]] = models.Manager()

    class Meta:
        """模型的元数据."""

        abstract = True
        ordering: ClassVar[list[str]] = ["-pk"]


class BaseModel(AbstractBaseModel):
    """项目模型的基类."""

    class Meta(AbstractBaseModel.Meta):
        """模型的元数据."""

        abstract = True


class OwnerModel(BaseModel):
    """有主人的模型: 冗余存用户 id, 用户名和头像."""

    user_id = models.PositiveIntegerField(
        _f("user", "id"), validators=[MinValueValidator(1)], default=1, editable=False
    )
    username = models.CharField(
        dj_gettext("username"), max_length=150, validators=[AbstractUser.username_validator], editable=False
    )  # 长度和Django的User保持一致
    user_avatar = models.URLField(_("avatar"), max_length=255, blank=True, editable=False)

    class Meta(BaseModel.Meta):
        """模型的元数据."""

        abstract = True


class PostModel(OwnerModel):
    """内容发布类模型."""

    title = models.CharField(_("title"), max_length=255)
    summary = models.CharField(_("summary"), max_length=2000, blank=True)
    images = models.CharField(_("images"), max_length=2000, blank=True)
    tags = models.CharField(_("tags"), max_length=255, blank=True)

    class Meta(OwnerModel.Meta):
        """模型的元数据."""

        abstract = True

    def __str__(self) -> str:
        """标题.

        Returns:
            标题.

        """
        return self.title


class ShardModel(OwnerModel):
    """按用户分库的模型: 主键里带用户 id."""

    id = models.BigAutoField(primary_key=True)

    class Meta(OwnerModel.Meta):
        """模型的元数据."""

        abstract = True

    def save(self, using: str | None = "default", *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        self.pk = self.pk or generate_shard_id(self.user_id)
        super().save(*args, using=db_master(self.user_id), **kwargs)


class ShardLCModel(OwnerModel):
    """按用户分库, 两个用户在不同库时各存一份的模型 (比如两人之间的卡片). 子类要有 card_id 字段."""

    id = models.BigAutoField(primary_key=True)
    is_origin = models.BooleanField(default=True)

    class Meta(OwnerModel.Meta):
        """模型的元数据."""

        abstract = True

    def save(self, using: str | None = "default", *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        self.pk = self.pk or generate_shard_id(self.user_id)
        super().save(*args, using=db_master(self.user_id), **kwargs)  # 保存第一份
        card_user_id = get_user_id(self.card_id)
        if db_master(card_user_id) != db_master(self.user_id):  # 保存第二份
            self.is_origin = False
            super().save(*args, using=db_master(card_user_id), **kwargs)
