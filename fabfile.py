import re
import shutil
from pathlib import Path

from fabric import task
from invoke import Context


@task
def cleanup(c: Context) -> None:
    """清理"""
    for p in Path().glob("**/*"):
        if p.is_dir():
            if p.name == "__pycache__" or not any(p.iterdir()):
                print(p)
                p.rmdir()
        elif p.name == ".DS_Store" or p.suffix == ".pyc":
            print(p)
            p.unlink()


@task
def distribute(c: Context) -> None:
    """发布到PyPI"""
    cleanup(c)
    # https://packaging.python.org/en/latest/tutorials/packaging-projects/
    c.run("uv build")
    c.run("uv publish --token $UV_PUBLISH_TOKEN")
    shutil.rmtree("dist")


@task
def fix(c: Context) -> None:
    """修复代码"""
    c.run("ruff check --fix")


@task(name="format")
def format_code(c: Context) -> None:
    """格式化代码"""
    c.run("ruff format")
    c.run("uvx isort .")
    for file in [f for d in ["src"] for f in (Path().cwd() / d).rglob("*.py")] + [Path(__file__)]:
        content = file.read_text("utf-8")
        new_content = re.sub(r",\s*\n(\s*)([])}])", r"\n\1\2", content)
        if new_content != content:
            file.write_text(new_content, "utf-8", newline="\n")


@task
def upgrade(c: Context) -> None:
    """升级"""
    remote, local = "https://raw.githubusercontent.com/nyssance/Free/main/", Path(__file__).parent
    c.run(f"curl -fsSL {remote}gitignore/Python.gitignore > {local / ".gitignore"}")
    c.run(f"curl -fsSL {remote}ruff.toml > {local / "ruff.toml"}")
