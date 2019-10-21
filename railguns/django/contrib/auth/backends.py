from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


# SO https://stackoverflow.com/questions/37332190/django-login-with-email#42848959
class ModelAndEmailBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            if '@' in username:
                user = UserModel._default_manager.get(email=username)
            else:
                user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
