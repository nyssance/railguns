import shutil
from pathlib import Path

from colorama import Fore, init
from fabric import task
from fabric.util import get_local_user

###########
# GLOBALS #
###########
PROJECT_NAME = Path(__file__).resolve(strict=True).parent.name
PROXY = '127.0.0.1:1087'


#########
# TASKS #
#########
@task(default=True, aliases=['别名测试'])
def hello(c, path='参数值'):
    init(autoreset=True)
    print('*' * 50)
    print(Fore.CYAN + '  Fabric 使用指南\n')
    print(Fore.GREEN + '  查看所有命令: fab -l')
    print(Fore.GREEN + '      查看命令: fab -d 命令')
    print(Fore.YELLOW + '    带参数命令: fab 命令 --参数 值\n')
    print(Fore.GREEN + '  Hello ~ ' + get_local_user())
    print('*' * 50)


@task
def local_cleanup(c):
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
def format(c):
    """格式化代码"""
    c.run('isort .')
    c.run('yapf -irp .')


@task
def pypi(c):
    """自动打包上传到 PyPI"""
    local_cleanup(c)
    c.run('python setup.py sdist')
    c.run('twine upload dist/*')
    shutil.rmtree('dist')


@task
def update(c):
    download(c, 'https://raw.githubusercontent.com/nyssance/Free/master/gitignore/Python.gitignore', '.gitignore')
    download(c, 'https://raw.githubusercontent.com/nyssance/Free/master/setup.cfg')
    c.run(f'sed -i "" "s|<project_name>|{PROJECT_NAME}|g" setup.cfg')


@task
def update_vendor(c):
    """更新前端库"""
    filenames = [
        'axios/axios.min.js', 'vue/vue.js', 'vue/vue.min.js', 'material-components-web/material-components-web.min.css',
        'material-components-web/material-components-web.min.js'
    ]
    for filename in filenames:
        download(c, f'https://unpkg.com/{filename.split("/")[0]}@latest/dist/{filename.split("/")[1]}',
                 f'{PROJECT_NAME}/static/vendor/{filename}')


def download(c, url, name=None):
    proxy = f' -x {PROXY}' if PROXY else ''
    command = f'{url} > {name}' if name else f'-O {url}'
    c.run(f'curl -fsSL{proxy} {command}')
