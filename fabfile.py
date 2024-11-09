import shutil
from pathlib import Path

from fabric import task


@task
def cleanup(c):
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
def distribute(c):
    """发布到PyPI"""
    cleanup(c)
    # https://packaging.python.org/en/latest/tutorials/packaging-projects/
    c.run("uv build")
    c.run("uv publish --token $UV_PUBLISH_TOKEN")
    shutil.rmtree("dist")


@task
def format_code(c):
    """格式化代码"""
    c.run("isort .")


@task
def upgrade(c):
    """升级"""
    c.run("curl -fsSL https://raw.githubusercontent.com/nyssance/Free/main/gitignore/Django.gitignore > .gitignore")
