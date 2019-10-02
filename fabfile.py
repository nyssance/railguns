import os
import shutil
from os.path import exists

from colorama import Fore, init
from fabric import task
from fabric.util import get_local_user
from invoke import env

###########
# GLOBALS #
###########
OS_ENVIRON = {e: os.environ.get(e) for e in os.environ}
PROJECT_NAME = os.path.basename(os.path.dirname(__file__))
PROXY = '127.0.0.1:1087'
env.colorize_errors = True


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
def format(c):
    """格式化代码"""
    c.run('isort -rc .')
    c.run('yapf -irp .')


@task
def pypi(c):
    """自动打包上传到 PyPI"""
    if exists('dist'):
        shutil.rmtree('dist')
    c.run('python setup.py sdist')
    c.run('twine upload dist/*')


@task
def update(c):
    curl(c, '-o .gitignore https://raw.githubusercontent.com/nyssance/Free/master/gitignore/Python.gitignore')
    curl(c, '-O https://raw.githubusercontent.com/nyssance/Free/master/setup.cfg')
    c.run(f'sed -i "" "s|<project_name>|{PROJECT_NAME}|g" setup.cfg')
    curl(c, '-O https://raw.githubusercontent.com/nyssance/Free/master/fabric.yaml')


@task
def update_vendor(c):
    """更新前端库"""
    filenames = [
        'axios/axios.min.js', 'vue/vue.js', 'vue/vue.min.js', 'material-components-web/material-components-web.min.css',
        'material-components-web/material-components-web.min.js'
    ]
    for filename in filenames:
        curl(
            c,
            f'https://unpkg.com/{filename.split("/")[0]}@latest/dist/{filename.split("/")[1]} > {PROJECT_NAME}/static/vendor/{filename}'
        )


# ============
# = 工具方法  =
# ============
def curl(c, command):
    proxy = f' -x {PROXY}' if PROXY else ''
    c.run(f'curl -fsSL{proxy} {command}')
