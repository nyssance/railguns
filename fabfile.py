# coding=utf-8

import os
import shutil

from fabric.colors import blue, cyan, green, magenta, red, yellow
from fabric.decorators import task
from fabric.operations import local
from fabric.state import env
from fabric.utils import puts

###########
# GLOBALS #
###########
env.project_name = os.path.basename(os.path.dirname(__file__))
env.colorize_errors = True
env.proxy = '127.0.0.1:1087'


#########
# TASKS #
#########
@task(default=True, alias='别名测试')
def hello():
    puts('*' * 50)
    puts(cyan('  Fabric 使用指南\n'))
    puts(green('  查看所有命令: fab -l'))
    puts(green('  查看命令: fab -d 命令'))
    puts(yellow('  带参数命令请输入: fab 命令:参数'))
    puts('  Project Name: {.project_name}'.format(env))  # 这种写法直观
    puts('*' * 50)


@task
def update_project():
    curl('https://raw.githubusercontent.com/nyssance/Free/master/gitignore/Python.gitignore > .gitignore')


@task
def local_format():
    local('isort -rc .')
    local('yapf -irp .')


@task
def local_update_vendor():
    """更新前端库"""
    filenames = [
        'axios.js', 'axios.min.js', 'vue.js', 'vue.min.js', 'material-components-web.min.css',
        'material-components-web.min.js'
    ]
    for filename in filenames:
        curl('https://unpkg.com/{0}@latest/dist/{1} > {2}/static/vendor/{1}'.format(
            filename.split('.')[0], filename, env.project_name))


# ========
# = PyPI =
# ========
@task
def upload_to_pypi():
    """自动打包上传到 PyPI"""
    safe_local_delete('dist')
    local('python setup.py sdist')
    local('twine upload dist/*')


# ============
# = 工具方法  =
# ============
def curl(command=''):
    local('curl -fsSL{} {}'.format(' -x {}'.format(env.proxy) if env.proxy else '', command))


def safe_local_delete(path):
    if os.path.exists(path):
        shutil.rmtree(path)
