import os
from importlib import import_module
from typing import override

from django.apps import AppConfig


class RailgunsConfig(AppConfig):
    """railguns 应用: 注册系统检查, 打开引擎的访问日志."""

    name = "railguns"
    verbose_name = "RailgunS"
    default_auto_field = "django.db.models.BigAutoField"  # 不取决于项目的 DEFAULT_AUTO_FIELD, 迁移才是固定的

    @override
    def ready(self) -> None:
        import_module(".checks", self.name)  # 导入就注册了系统检查

        # 访问日志由引擎在 Rust 里写到标准输出, 每个请求一行 JSON, 不经过 Python 的 logging
        os.environ["DJANGO_BOLT_ACCESS_LOG"] = "stdout"
