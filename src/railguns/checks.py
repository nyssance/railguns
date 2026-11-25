"""启动时的检查. 不符合约定就报错, manage.py check 和 runbolt 都不会通过.

- 数据库只能是 PostgreSQL.
- 每个数据库都必须配连接池. 不配的话每个线程各占一个连接, 进程一多就超过数据库的上限.
- 项目的模型不用外键: 没有 ForeignKey, OneToOneField, ManyToManyField. 别的表的行用 id 列引用 (比如 user_id).
  RAILGUNS_FOREIGN_KEY_APPS 里列出的应用 (app label) 不检查; 这个配置写错 (不是字符串列表, 应用没有安装) 也报错.
"""

import site
import sys
import sysconfig
from pathlib import Path
lazy from collections.abc import Sequence

from django.apps import AppConfig, apps
from django.conf import settings
from django.core.checks import CheckMessage, Error, Tags, register
from django.db.models import ForeignKey, ManyToManyField, Model, OneToOneField

from railguns.django.db._introspect import options


def errors_for(databases: dict[str, dict]) -> list[CheckMessage]:
    """每个数据库: 引擎是不是 PostgreSQL (E001), 有没有配连接池 (E002).

    Returns:
        错误, 没有错误时为空.

    """
    errors = []
    for alias, database in databases.items():
        engine = database.get("ENGINE", "")
        if "postgresql" not in engine:
            errors.append(
                Error(
                    f"数据库 {alias!r} 的引擎是 {engine!r}. 只支持 PostgreSQL.",
                    hint='ENGINE 改成 "django.db.backends.postgresql".',
                    id="railguns.E001",
                )
            )
        elif not database.get("OPTIONS", {}).get("pool"):
            errors.append(
                Error(
                    f"数据库 {alias!r} 没有配连接池.",
                    hint='在这个数据库的配置里加上 "OPTIONS": {"pool": {"min_size": 2, "max_size": 16}}.',
                    id="railguns.E002",
                )
            )
    return errors


@register()
def databases(app_configs: Sequence[AppConfig] | None, **kwargs: object) -> list[CheckMessage]:
    """配置里的数据库, 见 errors_for.

    Returns:
        错误, 没有错误时为空.

    """
    return errors_for(settings.DATABASES)


def installed_packages() -> list[Path]:
    """装第三方包的目录: 这个解释器的 site-packages (purelib, platlib) 和用户的 site-packages.

    Returns:
        解析过的目录.

    """
    paths = {sysconfig.get_paths()[name] for name in ("purelib", "platlib")}
    paths |= {*site.getsitepackages(), site.getusersitepackages()}
    return [Path(path).resolve() for path in paths]


def is_project(name: str, path: str | None, packages: list[Path] | None = None) -> bool:
    """项目自己的包或模块: 名字不是 django 或 django. 开头, 文件不在 site-packages 里.

    railguns 自己 (railguns 和 railguns.*) 装在哪里都算.

    Returns:
        是不是项目自己的.

    """
    if name == "railguns" or name.startswith("railguns."):
        return True
    if name == "django" or name.startswith("django."):
        return False
    if path is None:
        return True
    resolved = Path(path).resolve()
    return not any(resolved.is_relative_to(directory) for directory in packages or installed_packages())


def is_project_app(config: AppConfig, packages: list[Path] | None = None) -> bool:
    """项目自己的应用, 按应用的名字和目录 (见 is_project).

    Returns:
        是不是项目自己的.

    """
    return is_project(config.name, config.path, packages)


def declared_by(model: type[Model], name: str) -> type[Model]:
    """字段 name 是哪个类声明的.

    抽象基类的字段 Django 会复制到子类上, 所以沿 MRO 找最早声明它的抽象基类; 都没有就是模型自己.

    Returns:
        声明这个字段的类.

    """
    origin = model
    for base in model.__mro__[1:]:
        meta = getattr(base, "_meta", None)
        if (
            isinstance(base, type)
            and issubclass(base, Model)
            and meta is not None
            and meta.abstract
            and any(field.name == name for field in (*meta.local_fields, *meta.local_many_to_many))
        ):
            origin = base  # MRO 越往后越是更早的基类, 留下最后一个
    return origin


def declared_in_project(cls: type, packages: list[Path] | None = None) -> bool:
    """类是不是在项目自己的模块里声明的 (见 is_project).

    Returns:
        是不是项目自己的.

    """
    module = sys.modules.get(cls.__module__)
    return is_project(cls.__module__, getattr(module, "__file__", None), packages)


def relation_errors(models: list[type[Model]], packages: list[Path] | None = None) -> list[CheckMessage]:
    """模型的 ForeignKey, OneToOneField, ManyToManyField, 每个一条. 多表继承的父模型的字段算在父模型上.

    从抽象基类继承来的字段, 只有声明它的基类也是项目的 (见 declared_by, is_project) 才报:
    AbstractUser (PermissionsMixin) 的 groups, user_permissions 是 Django 声明的, 不报.
    多表继承自动加的 xxx_ptr 也是一对一 (数据库里是外键), 一样报错.

    Returns:
        错误 (E003), 每个外键一条.

    """
    errors = []
    packages = packages or installed_packages()
    for model in models:
        opts = options(model)
        for field in (*opts.local_fields, *opts.local_many_to_many):
            if not declared_in_project(declared_by(model, field.name), packages):
                continue
            if isinstance(field, ManyToManyField):
                kind, hint = "ManyToManyField", "另建一个模型, 用两个 id 列记下这两张表的行."
            elif isinstance(field, ForeignKey):
                kind = "OneToOneField" if isinstance(field, OneToOneField) else "ForeignKey"
                hint = f"改成普通的 id 列: {field.attname} = models.BigIntegerField()."
            else:
                continue
            errors.append(
                Error(
                    f"{opts.label}.{field.name} 是 {kind}. 模型之间不用外键, 资源只输出列和计算字段.",
                    hint=hint,
                    obj=model,
                    id="railguns.E003",
                )
            )
    return errors


def foreign_key_apps() -> tuple[set[str], list[CheckMessage]]:
    """RAILGUNS_FOREIGN_KEY_APPS: 允许用外键的应用 (app label), 默认没有. 写错时不放过任何应用, 并报 E004.

    Returns:
        (允许用外键的应用, 错误).

    """
    value = getattr(settings, "RAILGUNS_FOREIGN_KEY_APPS", ())
    if not isinstance(value, (list, tuple)) or not all(isinstance(label, str) for label in value):
        return set(), [
            Error(
                f"RAILGUNS_FOREIGN_KEY_APPS 是 {value!r}. 它必须是应用标签 (app label, 字符串) 的列表.",
                hint='比如 RAILGUNS_FOREIGN_KEY_APPS = ["architect"].',
                id="railguns.E004",
            )
        ]
    installed = {config.label for config in apps.get_app_configs()}
    if unknown := [label for label in value if label not in installed]:
        return set(), [
            Error(
                f"RAILGUNS_FOREIGN_KEY_APPS 里的这些应用没有安装: {unknown}.",
                hint=f"写 INSTALLED_APPS 里应用的标签 (app label), 已安装的有: {sorted(installed)}.",
                id="railguns.E004",
            )
        ]
    return set(value), []


@register()
def foreign_key_apps_setting(app_configs: Sequence[AppConfig] | None, **kwargs: object) -> list[CheckMessage]:
    """RAILGUNS_FOREIGN_KEY_APPS 写错时报 E004, 见 foreign_key_apps.

    Returns:
        错误, 没有错误时为空.

    """
    return foreign_key_apps()[1]


@register(Tags.models)
def relations(app_configs: Sequence[AppConfig] | None, **kwargs: object) -> list[CheckMessage]:
    """项目的应用 (见 is_project_app) 里的每个模型, RAILGUNS_FOREIGN_KEY_APPS 里的应用除外.

    app_configs 是 None 时看所有安装的应用. 指向这些应用的模型的外键, 声明在别的应用里照样报.

    Returns:
        错误 (E003), 见 relation_errors.

    """
    packages = installed_packages()
    exempt, _ = foreign_key_apps()
    configs = [
        config
        for config in app_configs or apps.get_app_configs()
        if config.label not in exempt and is_project_app(config, packages)
    ]
    return relation_errors([model for config in configs for model in config.get_models()], packages)
