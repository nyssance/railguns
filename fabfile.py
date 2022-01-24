import shutil
from pathlib import Path

from colorama import Fore, init
from fabric import task
from fabric.util import get_local_user

PROJECT_NAME = Path(__file__).resolve(strict=True).parent.name


@task
def cleanup(c):
    """清理"""
    for p in Path().glob('**/*'):
        if p.is_dir():
            if p.name == '__pycache__' or not any(p.iterdir()):
                print(p)
                p.rmdir()
        elif p.name == '.DS_Store' or p.suffix == '.pyc':
            print(p)
            p.unlink()


@task
def pypi(c):
    """自动打包上传到 PyPI"""
    cleanup(c)
    # https://packaging.python.org/en/latest/tutorials/packaging-projects/
    # c.run('python setup.py sdist')
    c.run('python3 -m build')
    # c.run('twine upload -r testpypi dist/*')
    c.run('twine upload dist/*')
    shutil.rmtree('dist')


@task
def reformat(c):
    """格式化"""
    c.run('isort .')
    c.run('yapf -irp .')


@task
def update(c):
    """更新"""
    c.run('curl -fsSL https://raw.githubusercontent.com/nyssance/Free/main/gitignore/Python.gitignore > .gitignore')
    c.run('curl -fsSL -O https://raw.githubusercontent.com/nyssance/Free/main/pyproject.toml')
    c.run(f'sed -i "" "s|<project-name>|{PROJECT_NAME}|g" pyproject.toml')
