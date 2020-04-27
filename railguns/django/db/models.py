from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..utils.translation import dj_gettext, format_gettext_lazy as _f
from .utils import db_master, generate_shard_id, get_user_id


class DateTimeModelMixin(models.Model):
    created_time = models.DateTimeField(_('created_time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated_time'), auto_now=True)

    class Meta:
        abstract = True


class AbstractBaseModel(DateTimeModelMixin):
    is_active = models.BooleanField(dj_gettext('active'), default=True)

    # 只是为了PyLint不警告, SO https://stackoverflow.com/questions/45135263/class-has-no-objects-member#45150811
    objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['-pk']


class BaseModel(AbstractBaseModel):

    class Meta(AbstractBaseModel.Meta):
        abstract = True


class OwnerModel(BaseModel):
    user_id = models.PositiveIntegerField(_f('user', 'id'),
                                          validators=[MinValueValidator(1)],
                                          default=1,
                                          editable=False)
    username = models.CharField(dj_gettext('username'),
                                max_length=150,
                                validators=[AbstractUser.username_validator],
                                editable=False)  # 长度和Django的User保持一致
    user_avatar = models.URLField(_('avatar'), max_length=255, blank=True, editable=False)

    class Meta(BaseModel.Meta):
        abstract = True


class PostModel(OwnerModel):
    """内容发布类模型"""
    title = models.CharField(_('title'), max_length=255)
    summary = models.CharField(_('summary'), max_length=2000, blank=True)
    images = models.CharField(_('images'), max_length=2000, blank=True)
    tags = models.CharField(_('tags'), max_length=255, blank=True)

    class Meta(OwnerModel.Meta):
        abstract = True

    def __str__(self):
        return self.title


class ShardModel(OwnerModel):
    id = models.BigAutoField(primary_key=True)

    class Meta(OwnerModel.Meta):
        abstract = True

    def save(self, using='default', *args, **kwargs):
        self.full_clean()
        self.pk = self.pk or generate_shard_id(self.user_id)
        super().save(using=db_master(self.user_id), *args, **kwargs)


class ShardLCModel(OwnerModel):
    id = models.BigAutoField(primary_key=True)
    is_origin = models.BooleanField(default=True)

    class Meta(OwnerModel.Meta):
        abstract = True

    def save(self, using='default', *args, **kwargs):
        self.full_clean()
        self.pk = self.pk or generate_shard_id(self.user_id)
        super().save(using=db_master(self.user_id), *args, **kwargs)  # 保存第一份
        card_user_id = get_user_id(self.card_id)
        if db_master(card_user_id) != db_master(self.user_id):  # 保存第二份
            self.is_origin = False
            super().save(using=db_master(card_user_id), *args, **kwargs)
