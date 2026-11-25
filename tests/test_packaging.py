"""打包: wheel 里要有运行时需要的每个文件. 完整的检查 (装进新环境跑测试) 见 scripts/check_wheel.sh."""

import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.skipif(not (shutil.which("uv") and (ROOT / "pyproject.toml").exists()), reason="需要 uv 和源码目录")
def test_the_wheel_has_the_migrations_and_the_commands() -> None:
    with tempfile.TemporaryDirectory() as folder:
        subprocess.run(["uv", "build", "--wheel", "--quiet", "--out-dir", folder, str(ROOT)], check=True)
        [wheel] = Path(folder).glob("railguns-*.whl")
        names = set(zipfile.ZipFile(wheel).namelist())
    expected = {
        "railguns/migrations/0001_initial.py",
        "railguns/management/commands/openapi.py",
        "railguns/management/commands/clearidempotencykeys.py",
        "railguns/apps.py",
    }
    assert expected <= names
