from os.path import abspath, dirname

from django.conf import settings


def get_name(file):
    return '.'.join(dirname(abspath(file)).replace(dirname(settings.PROJECT_PATH), '').split('/')[1:])
