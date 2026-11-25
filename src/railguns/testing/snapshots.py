import json
import os
from pathlib import Path
lazy from unittest import TestCase


def check_snapshot(test: TestCase, path: str | os.PathLike[str], actual: object) -> None:
    """和快照文件比对. 环境变量 UPDATE_SNAPSHOTS=1 时改为写入快照.

    快照不存在时会写入并让测试失败, 提醒把新快照检查后提交.
    """
    path = Path(path)
    update = os.environ.get("UPDATE_SNAPSHOTS") == "1"
    if update or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(actual, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
        if not update:
            test.fail(f"快照 {path.name} 不存在, 已写入, 检查后提交")
        return
    test.assertEqual(json.loads(path.read_text()), actual)
