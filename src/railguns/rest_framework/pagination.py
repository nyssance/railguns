"""分页. 资源接口的列表和业务接口用同一份代码: 参数, 上限, 404 和链接都一样.

业务接口的处理函数不声明 page / page_size. 返回类型是 Page[T] 的子类时, 接口定义里自动带上这两个参数:

    def sections(request) -> SectionPage:
        pagination = Pagination.of(request)  # 页码无效时 404
        count, rows = run(services.sections, actor(request), pagination.offset, pagination.size)
        return pagination.page(count, rows)   # 超出最后一页时 404
"""

from typing import Any, Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
lazy from collections.abc import Mapping

from django.conf import settings
from freeman.exceptions import HTTPException
from pydantic import BaseModel

PAGE_SIZE = getattr(settings, "REST_FRAMEWORK", {}).get("PAGE_SIZE") or 20
MAX_PAGE_SIZE = 1000


class PageRequest(Protocol):
    """分页用到的请求属性. 运行时是引擎的请求对象."""

    @property
    def query(self) -> Mapping[str, str]: ...

    def build_absolute_uri(self, location: str | None = None) -> str: ...


class Page[T](BaseModel):
    """列表的响应. 查询参数是 page (从 1 开始的数字) 和 page_size."""

    count: int
    next: str | None
    previous: str | None
    results: list[T]


def page_size(query: Mapping[str, str]) -> int:
    """每页条数. 不是正整数时用默认值, 超过上限时取上限.

    Returns:
        每页条数.

    """
    try:
        size = int(query.get("page_size", PAGE_SIZE))
    except TypeError, ValueError:
        return PAGE_SIZE
    return min(size, MAX_PAGE_SIZE) if size > 0 else PAGE_SIZE


def invalid_page() -> HTTPException:
    """页码无效时的 404.

    Returns:
        要抛出的异常.

    """
    return HTTPException(status_code=404, detail="无效页面。")


class Pagination:
    """一个请求的页码和每页条数, 以及这一页的响应."""

    def __init__(self, request: PageRequest) -> None:
        """从请求的查询参数里取页码和每页条数."""
        self.request = request
        self.size = page_size(request.query)
        try:
            self.number = int(request.query.get("page", 1))
        except TypeError, ValueError:
            self.number = 0
        self.valid = self.number >= 1  # 页码不是数字或者小于 1 时为 False. 资源接口先校验筛选值再报 404

    @classmethod
    def of(cls, request: PageRequest) -> Pagination:
        """这个请求的分页, 页码无效时 404.

        Returns:
            分页.

        Raises:
            invalid_page: 页码无效, 404.

        """
        pagination = cls(request)
        if not pagination.valid:
            raise invalid_page()
        return pagination

    @property
    def offset(self) -> int:
        """这一页第一行的下标.

        Returns:
            下标, 从 0 开始.

        """
        return (self.number - 1) * self.size

    def page(self, count: int, results: list) -> dict[str, Any]:
        """这一页的响应. 超出最后一页时 404. 第一页没有行时总数就是 0, 不算超出.

        Returns:
            {"count", "next", "previous", "results"}.

        Raises:
            invalid_page: 超出最后一页, 404.

        """
        if not results and self.number != 1:
            raise invalid_page()
        last = max(1, (count + self.size - 1) // self.size)
        return {
            "count": count,
            "next": self.link(self.number + 1, last),
            "previous": self.link(self.number - 1, last),
            "results": results,
        }

    def link(self, number: int, last: int) -> str | None:
        """第 number 页的绝对地址, 其余查询参数不变. 第一页不带 page.

        Returns:
            地址, 不在 1 到 last 之间时为 None.

        """
        if not 1 <= number <= last:
            return None
        parts = urlsplit(self.request.build_absolute_uri())
        pairs = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "page"]
        if number != 1:
            pairs.append(("page", str(number)))
        return urlunsplit(parts._replace(query=urlencode(pairs)))
