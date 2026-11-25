"""依赖引擎内部细节的代码都在这个文件里, 升级引擎时只需要核对这一个文件."""

import warnings
from importlib.metadata import version
lazy from collections.abc import Callable

lazy from freeman import BoltAPI

TESTED = ((0, 1), (0, 2))  # freeman >=0.1, <0.2


def check_version() -> None:
    """引擎的版本不在核对过的范围里时警告."""
    found = version("freeman")
    if not TESTED[0] <= tuple(int(part) for part in found.split(".")[:2]) < TESTED[1]:
        warnings.warn(
            f"railguns 只在 freeman {TESTED[0]} 到 {TESTED[1]} 之间核对过, 当前是 {found}", RuntimeWarning, stacklevel=2
        )


def routes(api: BoltAPI) -> list[tuple[str, str, Callable]]:
    """已注册的接口.

    Returns:
        [(请求方法, 路径, 处理函数)].

    """
    return [(method, path, handler) for method, path, _, handler in api._routes]


check_version()
