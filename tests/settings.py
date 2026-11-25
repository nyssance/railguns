"""测试用的最小项目. 数据库是 PostgreSQL, 用 DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT 指定."""

import getpass
import os
import tempfile

from railguns import conf

LOGGING = conf.LOGGING
SECRET_KEY = "railguns-tests-only-0123456789abcdef0123456789abcdef"
DEBUG = False
ALLOWED_HOSTS = ["*"]
USE_TZ = True
ROOT_URLCONF = "tests.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "railguns"),
        "USER": os.environ.get("DB_USER", getpass.getuser()),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {"pool": {"min_size": 1, "max_size": 8}},
    }
}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # 只为测试跑得快

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_ckeditor_5",
    "freeman",
    "railguns",
    "tests.app",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# railguns 读取的配置
API_VERSION = "v1"
SHARD_COUNT = 1
STATIC_URL = "https://static.example.com/"
MEDIA_URL = "https://media.example.com/"
MEDIA_ROOT = tempfile.gettempdir()
CLOUD_URL = "https://cloud.example.com/"
BUCKET_MEDIA = "media"
BUCKET_STATIC = "static"
BUCKET_CLOUD = "cloud"
CLOUD_STORAGE_DOMAIN_NAME = "oss.example.com"
CLOUD_STORAGE_REGION = "cn-test"
CLOUD_STORAGE_ID = "test-id"
CLOUD_STORAGE_SECRET = "test-secret"
RAILGUNS_LOGIN_PROFILE = "tests.app.services.profile"
