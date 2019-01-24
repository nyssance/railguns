import datetime
import inspect
import os
from typing import List

import stringcase
from django.conf import settings
from django.db.models import Model
from django.urls import URLPattern, URLResolver
from jinja2 import Environment, PackageLoader
from railguns.django.utils.translation import get_untranslated_text
from rest_framework.fields import (BooleanField, CharField, ChoiceField, DateField, DateTimeField, IntegerField,
                                   SerializerMethodField)
from rest_framework.mixins import ListModelMixin


class Property:
    name: str = None

    def __init__(self, key, type):
        self.key = key
        self.type = type
        self.name = stringcase.camelcase(key)

    @property
    def is_reference_type(self):
        return self.type not in ['bool', 'int', 'str', 'date']


class Path:

    def __init__(self, name, method, endpoint, params, model):
        self.name = name
        self.method = method
        self.endpoint = endpoint
        self.params = params
        self.model = model


def get_reference_type(key):
    for model in model_list:
        verbose_name = get_untranslated_text(model._meta.verbose_name)
        verbose_name_plural = get_untranslated_text(model._meta.verbose_name_plural)
        if key == verbose_name:
            return key.title()
        elif key == verbose_name_plural:
            return f'ListModel<{key.title()}>'
    return 'str'


def generate_api_service(language: str, top: str):
    """生成 APIService 文件"""
    project_name = settings.PROJECT_NAME
    java_package_name = '.'.join(settings.DOMAIN_NAME.split('.')[::-1])
    version = settings.REST_FRAMEWORK['DEFAULT_VERSION']
    # Jinja2
    # env = Environment(loader=PackageLoader(project_name, 'apps/developer/templates'))
    env = Environment(loader=PackageLoader('railguns', 'developer/templates'))
    env.globals.update({'year': datetime.datetime.today().year})
    os.makedirs(os.path.join(top), exist_ok=True)
    template = env.get_template(f'APIService.{language}')
    #
    exec(f'import {project_name}')

    patterns: List[URLPattern] = []
    for url in eval(f'{project_name}.apps.api.urls.urlpatterns'):
        if isinstance(url, URLResolver):
            patterns += url.url_patterns  # 不考虑多层include
        else:
            patterns.append(url)

    paths: List[Path] = []
    for url in patterns:
        view = url.callback.view_class
        serializer = getattr(view, 'serializer_class', None)
        name = url.name.replace('api-', '', 1).replace('-', '_')
        endpoint = f'api/{version}/{url.pattern}'
        model = serializer.Meta.model.__name__ if serializer else name.split('_')[0].title()  # 没有 serializer_class，推断类型
        if issubclass(view, ListModelMixin):  # 列表
            model = f'PagingList<{model}>'
        methods = view().allowed_methods
        for method in filter(lambda x: x not in ['OPTIONS', 'PUT'], methods):
            if method == 'PATCH' and 'GET' in methods:
                name = f'{name}_update'
            params: str = None
            if '<int:pk>' in endpoint:
                if language == 'kt':
                    endpoint = endpoint.replace('<int:pk>', '{id}')
                    params = '@Path("id") id: Long'
                elif language == 'swift':
                    endpoint = endpoint.replace('<int:pk>', '\(id)')
                    params = '_ id: Int'
            paths.append(Path(stringcase.camelcase(name), method, endpoint, params, model))
    # 写入文件
    with open(os.path.join(top, f'APIService.{language}'), 'w') as file:
        file.write(template.render(package=java_package_name, paths=paths))


def generate_model(language: str, top: str, modules: List[str] = None) -> str:
    """生成 模型类"""
    modules = modules if modules else []
    project_name = settings.PROJECT_NAME
    java_package_name = '.'.join(settings.DOMAIN_NAME.split('.')[::-1])
    # Jinja2
    # env = Environment(extensions=['jinja2.ext.do', 'jinja2.ext.i18n'], loader=PackageLoader(project_name, 'apps/developer/templates'))
    env = Environment(extensions=['jinja2.ext.do', 'jinja2.ext.i18n'], loader=PackageLoader('railguns', 'developer/templates'))
    env.globals.update({'year': datetime.datetime.today().year})
    model_path = 'Model' if language == 'swift' else 'model'
    os.makedirs(os.path.join(top, model_path), exist_ok=True)
    template = env.get_template(f'Model.{language}')
    #
    exec(f'import {project_name}')
    # 获取用到的模型类, 包括级联
    for module in modules:
        module_name = f'{project_name}.{module}'
        global model_list
        model_list = []
        for member in inspect.getmembers(eval(module_name), inspect.isclass):
            if issubclass(member[1], Model):
                model_list.append(member[1])
    # 生成 {kotlin,swift} 模型类文件
    for module in modules:
        module_name = f'{project_name}.{module}'
        for member in inspect.getmembers(eval(module_name), inspect.isclass):
            class_name = f'{module_name}.{member[0]}'
            if class_name.endswith('DetailSerializer'):
                name = eval(f'{class_name}().Meta.model.__name__')
                env.globals.update({'name': name})
                fields = eval(f'{class_name}().fields')
                properties = []
                for key, value in fields.items():
                    type_name = None
                    if isinstance(value, BooleanField):
                        type_name = 'bool'
                    elif isinstance(value, IntegerField):
                        type_name = 'int'
                    elif isinstance(value, (DateField, DateTimeField)):
                        type_name = 'date'
                    elif isinstance(value, CharField):
                        type_name = 'str'
                    elif isinstance(value, ChoiceField):  # next(iter(value.choices)) 获取choices第一个key
                        type_name = type(next(iter(value.choices))).__name__
                    elif isinstance(value, SerializerMethodField):
                        type_name = get_reference_type(key)
                    type_name = type_name if type_name else type(value).__name__
                    if not key.endswith('id_str'):
                        properties.append(Property(key, type_name))
                # 写入文件
                with open(os.path.join(top, model_path, f'{name}.{language}'), 'w') as file:
                    file.write(template.render(package=java_package_name, properties=properties))
    return top
