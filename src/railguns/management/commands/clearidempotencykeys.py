"""删掉过期的幂等键.

定时运行, 比如每小时一次:

python manage.py clearidempotencykeys
"""

from typing import override

from django.core.management.base import BaseCommand
from django.utils import timezone

from railguns.models import IdempotencyKey
from railguns.rest_framework.idempotency import TTL


class Command(BaseCommand):
    """manage.py clearidempotencykeys."""

    help = "删掉过期 (超过 24 小时) 的幂等键."

    @override
    def handle(self, *args: str, **options: object) -> None:
        deleted, _ = IdempotencyKey.objects.filter(created_time__lt=timezone.now() - TTL).delete()
        self.stdout.write(f"删掉了 {deleted} 个过期的幂等键.")
