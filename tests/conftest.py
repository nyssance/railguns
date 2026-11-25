"""pytest 的公共夹具."""

lazy from collections.abc import Iterator

import pytest
from django.db import connections
from django.db.backends.postgresql.base import DatabaseWrapper as PostgreSQLWrapper
from freeman.postgres import close_all_pools
from freeman.testing import TestClient

from .app.api import api


@pytest.fixture(scope="session")
def close_pools(django_db_setup: None) -> Iterator[None]:
    """删测试库之前先把池关掉: 池里空闲的连接会让删库失败. 和 railguns.testing.runner.Runner 做的一样.

    pyproject.toml 的 usefixtures 让每个测试都用它.

    Yields:
        测试会话期间什么也不做.

    """
    yield
    close_all_pools()
    for connection in connections.all(initialized_only=True):
        connection.close()
        if isinstance(connection, PostgreSQLWrapper):  # 只支持 PostgreSQL (railguns.E001), 连接池在它上面
            connection.close_pool()


@pytest.fixture
def client(transactional_db: None) -> Iterator[TestClient]:
    """接口的测试客户端. 处理函数在 Bolt 的线程里用自己的数据库连接, 所以数据必须真的提交: transactional_db.

    Yields:
        不共享测试连接的 TestClient.

    """
    with TestClient(api, raise_server_exceptions=False, share_db_connection=False) as client:
        yield client
