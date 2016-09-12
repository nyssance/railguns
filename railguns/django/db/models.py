from django.db import models
from django.utils.translation import ugettext_lazy as _

from .utils import generate_shard_id, get_user_id, db_master


class DateTimeModelMixin(models.Model):
    created_time = models.DateTimeField(_('created_time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated_time'), auto_now=True)

    class Meta:
        abstract = True


class OwnerModel(DateTimeModelMixin):
    user_id = models.IntegerField(default=0, editable=False)
    username = models.CharField(max_length=150, editable=False)
    user_image_urls = models.CharField(_('image_urls'), max_length=2000, blank=True, editable=False)
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        abstract = True
        ordering = ['-pk']


class PostModel(OwnerModel):
    """内容发布类模型"""
    title = models.CharField(_('title'), max_length=30)
    summary = models.CharField(_('summary'), max_length=200, blank=True)
    image_urls = models.CharField(_('image_urls'), max_length=2000, blank=True)
    tags = models.CharField(_('tags'), max_length=200, blank=True)

    class Meta(OwnerModel.Meta):
        abstract = True

    def __str__(self):
        return self.title


class ShardModel(OwnerModel):
    id = models.BigIntegerField(primary_key=True, editable=False)

    class Meta(OwnerModel.Meta):
        abstract = True

    def save(self, using='default', *args, **kwargs):
        self.full_clean()
        if self.pk is None:
            self.pk = generate_shard_id(self.user_id)
        super(ShardModel, self).save(using=db_master(self.user_id), *args, **kwargs)


class ShardLCModel(OwnerModel):
    id = models.BigIntegerField(primary_key=True, editable=False)
    is_origin = models.BooleanField(default=True)

    class Meta(OwnerModel.Meta):
        abstract = True

    def save(self, using='default', *args, **kwargs):
        self.full_clean()
        if self.pk is None:  # Create
            self.pk = generate_shard_id(self.user_id)
        super(ShardLCModel, self).save(using=db_master(self.user_id), *args, **kwargs)  # 保存第一份.
        card_user_id = get_user_id(self.card_id)
        if db_master(card_user_id) != db_master(self.user_id):  # 保存第二份.
            self.is_origin = False
            super(ShardLCModel, self).save(using=db_master(card_user_id), *args, **kwargs)
