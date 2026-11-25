import json
lazy from collections.abc import Iterable, Sequence

from django.test import Client, TransactionTestCase
from freeman.testing import TestClient
lazy from freeman.api import BoltAPI

type Case = tuple[str, str, str | None, object]
"""(方法, 路径, self 上的用户属性名或 None, 请求体或 None)."""
type Result = tuple[int, object]
"""(状态码, 去掉易变字段的响应体)."""


class ParityTestCase(TransactionTestCase):
    """迁移期间比对新旧两套实现.

    旧实现还挂在 Django 的路由里, 新实现注册在 Bolt 上, 路径相同. 同一个请求两边各发一次, 状态码和响应体必须一致.
    每一边都从干净的数据库重新 seed, 所以写操作也能比.

        class OrderParityTests(ParityTestCase):
            api = project_api

            def seed(self):
                self.buyer = User.objects.create_user("buyer")

            def old_headers(self, user): ...   # 旧实现认的凭证
            def new_headers(self, user): ...   # 新实现认的凭证

            def test_create(self):
                self.assert_parity([("post", "/api/v1/orders", "buyer", {"sku": 1})])
    """

    api: BoltAPI | None = None
    reset_sequences = True
    volatile = ("created_time", "updated_time")  # 两次运行本来就会不同的字段, 比对时忽略其值

    def seed(self) -> None:
        """建测试数据. 每一边开始前在空库上调用一次."""

    def old_headers(self, user: object) -> dict:
        """旧实现认的凭证.

        Returns:
            请求头.

        """
        return {}

    def new_headers(self, user: object) -> dict:
        """新实现认的凭证.

        Returns:
            请求头.

        """
        return {}

    def reset(self) -> None:
        self._fixture_teardown()
        self._fixture_setup()
        self.seed()

    def scrub(self, value: object) -> object:
        """把易变字段的值换成 <volatile>.

        Returns:
            换过的值.

        """
        if isinstance(value, dict):
            return {
                k: "<volatile>" if k in self.volatile and v is not None else self.scrub(v) for k, v in value.items()
            }
        if isinstance(value, list):
            return [self.scrub(item) for item in value]
        return value

    def body(self, content: bytes) -> object:
        """解析响应体, 不是 JSON 时取前 200 个字节.

        Returns:
            去掉易变字段的响应体.

        """
        try:
            return self.scrub(json.loads(content)) if content else None
        except ValueError:
            return content[:200]

    def old(self, method: str, path: str, user: object, data: object) -> Result:
        """用 Django 的测试客户端请求旧实现.

        Returns:
            状态码和响应体.

        """
        client = Client(raise_request_exception=False, headers=self.old_headers(user) if user else {})
        kwargs = {} if data is None else {"data": json.dumps(data), "content_type": "application/json"}
        response = getattr(client, method)(path, **kwargs)
        return response.status_code, self.body(response.content)

    def new(self, method: str, path: str, user: object, data: object) -> Result:
        """用 Bolt 的测试客户端请求新实现.

        Returns:
            状态码和响应体.

        """
        kwargs = {} if data is None else {"json": data}
        with TestClient(self.api, raise_server_exceptions=False, share_db_connection=False) as client:
            response = client.request(method.upper(), path, headers=self.new_headers(user) if user else {}, **kwargs)
        return response.status_code, self.body(response.content)

    def compare(self, case: Case, old: Result, new: Result, mismatches: list[str]) -> None:
        """两边的结果不同时记到 mismatches 里."""
        # 未处理的异常两边都是 500, 但错误页是各框架自己的, 只比状态码
        same = old[0] == new[0] if old[0] >= 500 and new[0] >= 500 else old == new
        if not same:
            method, path, actor, data = case
            mismatches.append(f"{method.upper()} {path} as {actor} {data}\n    old: {old}\n    new: {new}")

    def assert_parity(self, cases: Iterable[Case]) -> None:
        """每个请求互不相关: 每个请求两边都从刚 seed 的数据库开始.

        cases: (方法, 路径, self 上的用户属性名或 None, 请求体或 None).
        """
        mismatches = []
        for case in cases:
            results = []
            for side in (self.old, self.new):
                self.reset()
                method, path, actor, data = case
                results.append(side(method, path, getattr(self, actor) if actor else None, data))
            self.compare(case, *results, mismatches)
        self.assertFalse(mismatches, "\n" + "\n".join(mismatches))

    def assert_flow(self, cases: Sequence[Case]) -> None:
        """一串有先后关系的请求: 每一边 seed 一次, 按顺序发完, 后面的读请求可以验证前面的写入."""
        results = []
        for side in (self.old, self.new):
            self.reset()
            results.append([
                side(method, path, getattr(self, actor) if actor else None, data) for method, path, actor, data in cases
            ])
        mismatches = []
        for case, old, new in zip(cases, *results, strict=True):
            self.compare(case, old, new, mismatches)
        self.assertFalse(mismatches, "\n" + "\n".join(mismatches))
