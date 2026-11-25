"""接口定义 (OpenAPI) 的导出和破坏性变更检查. 三端的类型都从这一份文件生成.

    python manage.py openapi                          # 写到 openapi.json
    python manage.py openapi --check                  # 和已提交的 openapi.json 比, 不一致就失败
    python manage.py openapi --breaking origin/main   # 和某个提交里的 openapi.json 比, 有破坏性变更就失败

约定:

- openapi.json 提交进仓库. 接口一改, 它就跟着变, 评审时能直接看到接口的差异.
- CI 里跑 --check (定义和代码一致) 和 --breaking (没有破坏已发布的客户端).
- 破坏性变更由 oasdiff 判定: 删接口, 删字段, 改类型, 新增必填参数等.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import override

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from freeman.management.commands.runbolt import Command as RunBolt
from freeman.openapi import OpenAPIConfig

from railguns.rest_framework.schemas.openapi import AutoSchema

DEFAULT_PATH = "openapi.json"


def document() -> dict:
    """项目的接口定义. 找接口入口的方式和 runbolt 一样, 所以文档里的就是服务器上的.

    Returns:
        OpenAPI 文档.

    Raises:
        CommandError: 没有找到接口入口.

    """
    runner = RunBolt()
    apis = runner.autodiscover_apis()
    if not apis:
        msg = "没有找到接口入口. 在项目的 api.py 里写 api = API()."
        raise CommandError(msg)
    api = runner.merge_apis(apis) if len(apis) > 1 else apis[0][1]
    title = getattr(settings, "API_TITLE", None) or Path(settings.ROOT_URLCONF.split(".")[0]).name
    config = OpenAPIConfig(title=title, version=str(getattr(settings, "API_VERSION", "v1")))
    return AutoSchema(api, config).generate()


def dumps(schema: dict) -> str:
    """固定的写法: 两格缩进, 末尾换行. 同样的接口每次导出的文件完全一样.

    不给键排序: 字段按模型里声明的顺序出现, 生成的客户端里构造函数的参数也是这个顺序.

    Returns:
        JSON 文本.

    """
    return json.dumps(schema, ensure_ascii=False, indent=2) + "\n"


class Command(BaseCommand):
    """manage.py openapi."""

    help = "导出接口定义, 检查它和代码是否一致, 检查有没有破坏性变更."

    @override
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--out", default=DEFAULT_PATH, help=f"接口定义文件, 默认 {DEFAULT_PATH}")
        parser.add_argument("--check", action="store_true", help="不写文件. 文件和代码不一致时失败")
        parser.add_argument(
            "--breaking", metavar="BASE", help="和 BASE 比, 有破坏性变更时失败. BASE 是文件路径或 git 提交"
        )

    @override
    def handle(self, *args: str, out: str, check: bool, breaking: str | None, **options: object) -> None:
        path = Path(out)
        current = dumps(document())
        if breaking:
            self.breaking(breaking, path, current)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != current:
                msg = f"{path} 和代码不一致. 运行 python manage.py openapi 重新导出, 并提交."
                raise CommandError(msg)
            self.stdout.write(f"{path} 和代码一致.")
        elif not breaking:
            path.write_text(current, encoding="utf-8")
            self.stdout.write(f"已写入 {path}.")

    def breaking(self, base: str, path: Path, current: str) -> None:
        oasdiff = shutil.which("oasdiff")
        if not oasdiff:
            msg = "需要 oasdiff: brew install oasdiff, 或见 https://github.com/oasdiff/oasdiff"
            raise CommandError(msg)
        with tempfile.TemporaryDirectory() as folder:
            new = Path(folder) / "new.json"
            new.write_text(current, encoding="utf-8")
            old = Path(base)
            if not old.is_file():  # 不是文件就当成 git 提交, 取那个提交里的接口定义
                command = ["git", "show", f"{base}:{path.as_posix()}"]
                shown = subprocess.run(command, capture_output=True, text=True, check=False)
                if shown.returncode:
                    msg = f"{base} 既不是文件, 也不是包含 {path} 的 git 提交."
                    raise CommandError(msg)
                old = Path(folder) / "old.json"
                old.write_text(shown.stdout, encoding="utf-8")
            command = [oasdiff, "breaking", str(old), str(new), "--fail-on", "ERR"]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode:
            raise CommandError("有破坏性变更:\n" + (result.stdout or result.stderr).strip())
        self.stdout.write("没有破坏性变更.")
