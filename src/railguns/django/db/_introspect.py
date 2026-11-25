"""读模型的元数据和默认管理器. Django 公开的 API 是 _meta 和 _default_manager, 名字带下划线, 访问都放在这里.

只用在启动时或者有缓存的地方; 每个请求都走的代码直接访问, 省一次函数调用.
"""

from django.db.models import Manager, Model
lazy from django.db.models.options import Options


def options[M: Model](model: type[M] | M) -> Options[M]:
    """模型的元数据 (_meta).

    Returns:
        模型的 Options.

    """
    return model._meta


def default_manager[M: Model](model: type[M]) -> Manager[M]:
    """模型的默认管理器 (_default_manager).

    Returns:
        默认管理器.

    """
    return model._default_manager
