from typing import ClassVar

from django.db import models


class IdempotencyKey(models.Model):
    """一个用过的幂等键, 和它第一次请求的响应 (见 rest_framework.idempotency).

    只有成功的请求才有这一行, 并且和那次请求写入的数据在同一个事务里提交: 请求失败时它跟着回滚, 客户端可以重试.
    不会重复执行靠的是 (user_id, key) 上的唯一约束, 不靠 Python 里先查再插.
    """

    user_id = models.BigIntegerField()
    key = models.CharField(max_length=255)
    fingerprint = models.CharField(max_length=64)  # 请求方法, 路径, 请求体的 SHA-256
    status_code = models.PositiveSmallIntegerField()
    body = models.BinaryField()
    created_time = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        """(user_id, key) 唯一."""

        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(fields=("user_id", "key"), name="railguns_idempotency_key_unique")
        ]

    def __str__(self) -> str:
        """用户和键, 和咨询锁用的字符串一样.

        Returns:
            "user_id:key".

        """
        return f"{self.user_id}:{self.key}"
