import socket
import uuid
from unittest import mock
from urllib.parse import urlparse

from django.conf import settings
from django.test import override_settings

LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")


class NetworkBlocked(Exception):
    """测试里发起了外部连接."""


def service_ports() -> set[int]:
    """测试允许连接的端口: 配置里的数据库和缓存.

    Returns:
        端口的集合.

    """
    ports = {int(db["PORT"]) for db in settings.DATABASES.values() if db.get("PORT")}
    for cache in settings.CACHES.values():
        location = cache.get("LOCATION")
        for url in [location] if isinstance(location, str) else location or []:
            if port := urlparse(url).port:
                ports.add(port)
    return ports


def block_external_network() -> mock._patch:
    """只放行本机的数据库和缓存, 测试里任何其他网络连接都直接报错, 保证不会打到真实的第三方.

    Returns:
        替换 socket.socket.connect 的 patch, 用作上下文管理器或装饰器.

    """
    connect = socket.socket.connect
    ports = service_ports()

    def guarded(self: socket.socket, address: tuple | str | bytes, *args: object, **kwargs: object) -> None:
        if isinstance(address, tuple) and not (address[0] in LOCAL_HOSTS and address[1] in ports):
            msg = f"测试里发起了外部连接: {address[0]}:{address[1]}"
            raise NetworkBlocked(msg)
        return connect(self, address, *args, **kwargs)

    return mock.patch.object(socket.socket, "connect", guarded)


def isolated_caches() -> override_settings:
    """每次运行用独立的缓存前缀, 限流计数和锁都从零开始, 结果不受上一次运行影响.

    Returns:
        改了 CACHES 的 override_settings, 用作上下文管理器或装饰器.

    """
    prefix = f"test-{uuid.uuid4().hex}"
    return override_settings(
        CACHES={alias: {**config, "KEY_PREFIX": prefix} for alias, config in settings.CACHES.items()}
    )
