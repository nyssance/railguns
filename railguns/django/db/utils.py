import datetime
import time

from django.conf import settings
from django.utils import timezone


def timestamp(date):
    return time.mktime(date.timetuple())


def generate_shard_id(user_id):
    time_offset = int(timestamp(datetime.datetime.now()) - 1425168000)  # 2015-03-01 00:00:00
    return user_id | time_offset << 32


def get_object_or_none(model, using='default', **kwargs):
    try:
        return model.objects.using(using).get(**kwargs)
    except model.DoesNotExist:
        return None


def get_pk_int(view):
    """
    必须转为int否则不等于request.user.id, int必须有值安全起见设默认值0
    """
    return int(view.kwargs.get('pk', 0))


def get_user_id(pk):
    """
    需要保证传入的pk都是int, 所以在views中需要和和get_pk_int配合使用
    """
    return pk & 0xFFFFFFFF


def db_master(user_id=None):
    """
    需要保证传入的user_id都是int
    """
    if not user_id:
        return 'default'
    else:
        if user_id < 10000:
            return 'default'
        else:
            return 'db_{}'.format(user_id % settings.SHARD_COUNT)


def db_slave(user_id=None):
    suffix = ''
    return '{}{}'.format(db_master(user_id), suffix)  # replica_


def redis_master(user_id=None):
    if not user_id:
        return 0
    else:
        if user_id < 10000:
            return 0
        else:
            return int(user_id / 1000)


def datetime_to_unixtime(date_time):
    created_str = date_time.strftime('%Y-%m-%d %H:%M:%S')
    date_time = datetime.datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=8)
    return int(time.mktime(date_time.timetuple()))


def unixtime_to_datetime(local_time):
    date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(local_time))
    date_time = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return date_time


def unixtime_to_date(local_time):
    date_str = time.strftime('%Y-%m-%d', time.localtime(local_time))
    return date_str


def datetime_timezone_zero():
    return datetime.datetime(timezone.now().year, timezone.now().month, timezone.now().day, 0, 0, 0)


def string_to_unixtime(string):
    date_time = datetime.datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
    time_time = int(time.mktime(date_time.timetuple()))
    return time_time
