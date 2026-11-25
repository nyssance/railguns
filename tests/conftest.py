"""pytest 的公共夹具."""

lazy from collections.abc import Iterator

import pytest
from freeman.testing import TestClient

from .app.api import api


@pytest.fixture
def client(transactional_db: None) -> Iterator[TestClient]:
    """接口的测试客户端. 处理函数在 Bolt 的线程里用自己的数据库连接, 所以数据必须真的提交: transactional_db.

    Yields:
        不共享测试连接的 TestClient.

    """
    with TestClient(api, raise_server_exceptions=False, share_db_connection=False) as client:
        yield client
