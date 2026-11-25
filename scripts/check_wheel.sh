#!/bin/sh
# 装好的包能用: 打出 wheel, 和 freeman 一起装进一个新的虚拟环境, 用装好的包跑一遍测试.
# 测试的代码复制到临时目录里运行, 导入的 railguns 是装好的那份, 不是 src/. 少打包了文件 (比如迁移) 这里就会失败.
#
#   sh scripts/check_wheel.sh
#
# FREEMAN: freeman 的 wheel 或源码目录, 默认 ../freeman. 源码目录先复制出来再构建, 构建产物不写进 freeman 的目录.
# 数据库和测试一样用 DB_* 环境变量, 测试库是 test_railguns_wheel, 测试结束时删掉.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
FREEMAN=${FREEMAN:-$ROOT/../freeman}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

uv build --wheel --quiet --out-dir "$WORK/dist" "$ROOT"
uv venv --quiet --python 3.15 "$WORK/venv"
PY="$WORK/venv/bin/python"
if [ -d "$FREEMAN" ]; then
  rsync -a --exclude target --exclude .venv --exclude .git --exclude dist "$FREEMAN/" "$WORK/freeman/"
  FREEMAN="$WORK/freeman"
fi
uv pip install --quiet --python "$PY" "$WORK"/dist/railguns-*.whl "$FREEMAN" pytest pytest-django

mkdir "$WORK/project"
cp -R "$ROOT/tests" "$WORK/project/tests"
find "$WORK/project" -name __pycache__ -prune -exec rm -rf {} +
cd "$WORK/project"
export DJANGO_SETTINGS_MODULE=tests.settings DB_NAME="${DB_NAME:-railguns_wheel}"
"$PY" - <<'PY'
import django

django.setup()
import railguns
from django.db.migrations.loader import MigrationLoader

assert "site-packages" in railguns.__file__, f"导入的不是装好的包: {railguns.__file__}"
assert ("railguns", "0001_initial") in MigrationLoader(None).disk_migrations, "wheel 里没有 railguns 的迁移"
print("装好的包:", railguns.__file__)
PY
# 不复制 pyproject.toml (有它 test_packaging 会去构建这个目录), pytest 的配置在命令行上给: 和 [tool.pytest.ini_options] 一样
"$PY" -m pytest -q -p no:cacheprovider --create-db -o python_files="test_*.py" -o usefixtures=close_pools tests
