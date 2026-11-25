"""验证工具: 证明接口的行为没有变.

- matrix: 每条路由 x 每种身份的状态码 (权限矩阵)
- contract: 每个序列化器的字段契约 (类型 / 必填 / 只读)
- parity: 迁移期间新旧两套实现逐个请求比对
- snapshots: 以上结果存成快照文件, 以后每次运行和快照比

升级框架, 换库, 重写接口之前先录一份快照, 改完再跑, 有差异的地方就是行为变了的地方.
"""

from .contract import serializer_contract
from .guards import block_external_network, isolated_caches
from .matrix import access_matrix
from .parity import ParityTestCase
from .snapshots import check_snapshot

__all__ = [
    "ParityTestCase",
    "access_matrix",
    "block_external_network",
    "check_snapshot",
    "isolated_caches",
    "serializer_contract",
]
