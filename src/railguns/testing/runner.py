from django.db import connections
from django.db.backends.postgresql.base import DatabaseWrapper as PostgreSQLWrapper
from django.test.runner import DiscoverRunner
from freeman.postgres import close_all_pools


class Runner(DiscoverRunner):
    """项目的测试运行器: settings 里写 TEST_RUNNER = "railguns.testing.runner.Runner".

    数据库必须配连接池, 而池里空闲的连接会让 Django 删不掉测试库. 所以删库之前先把池关掉:
    读接口用的原生连接池, 和 Django 自己的连接池.
    """

    def teardown_databases(self, old_config: list, **kwargs: object) -> None:
        close_all_pools()
        for connection in connections.all(initialized_only=True):
            connection.close()
            if isinstance(connection, PostgreSQLWrapper):  # 只支持 PostgreSQL (railguns.E001), 连接池在它上面
                connection.close_pool()
        super().teardown_databases(old_config, **kwargs)
