import shutil
from pathlib import Path

from fabric import task

PROJECT_NAME = Path(__file__).resolve(strict=True).parent.name


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
    """发布到 PyPI"""
    cleanup(c)
    # https://packaging.python.org/en/latest/tutorials/packaging-projects/
    c.run("pyproject-build")
    c.run("twine upload dist/*")
    shutil.rmtree("dist")


@task
def format_code(c):
    """格式化代码"""
    c.run("isort .")
    c.run("yapf -irp .")


@task
def update(c):
    """更新"""
    c.run("curl -fsSL https://raw.githubusercontent.com/nyssance/Free/main/gitignore/Django.gitignore > .gitignore")
