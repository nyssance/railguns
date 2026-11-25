"""项目可直接引用的默认配置.

from railguns.conf import LOGGING
"""

# 访问日志由引擎在 Rust 里写到标准输出 (railguns 启动时打开), 每个请求一行 JSON.
# Python 的 `django.server` 只记错误: 经过 Python 的 logging 记访问日志, 空接口的吞吐只剩三成.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django.server": {"handlers": ["console"], "level": "ERROR", "propagate": False}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
