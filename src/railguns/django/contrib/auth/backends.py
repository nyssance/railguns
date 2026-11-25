from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
lazy from django.contrib.auth.models import AbstractBaseUser
lazy from django.http import HttpRequest

from railguns.django.db._introspect import default_manager


# SO https://stackoverflow.com/questions/37332190/django-login-with-email#42848959
class ModelAndEmailBackend(ModelBackend):
    """用户名或邮箱登录: 用户名里有 @ 时按邮箱找用户."""

    def authenticate(
        self, request: HttpRequest | None, username: str | None = None, password: str | None = None, **kwargs: object
    ) -> AbstractBaseUser | None:
        user_model = get_user_model()
        if username is None:
            username = kwargs.get(user_model.USERNAME_FIELD)
        if username is None or password is None:  # 和 ModelBackend 一样: 没给用户名或密码时不认证
            return None
        try:
            if "@" in username:
                user = default_manager(user_model).get(email=username)
            else:
                user = default_manager(user_model).get_by_natural_key(username)
        except user_model.DoesNotExist:
            user_model().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
