import datetime
import time
from typing import Optional

from django.conf import settings
from django.utils import timezone


def timestamp(date):
    return time.mktime(date.timetuple())


def generate_shard_id(user_id: int) -> int:
    time_offset = int(timestamp(datetime.datetime.now()) - 1510358400)  # 2017-11-11 00:00:00 中国时间
    return user_id | time_offset << 32


def get_object(model, using='default', default=None, **kwargs):
    try:
        return model.objects.using(using).get(**kwargs)
    except model.DoesNotExist:
        return default


def get_user_id(pk: int) -> int:
    """
    需要保证传入的pk都是int
    """
    return pk & 0xFFFFFFFF


def db_master(user_id: Optional[int] = None) -> str:
    """
    需要保证传入的user_id都是int
    """
    if not user_id:
        return 'default'
    else:
        if user_id < 100001:
            return 'default'
        else:
            return f'db_{user_id % settings.SHARD_COUNT}'


def db_slave(user_id: Optional[int] = None) -> str:
    suffix = ''
    return f'{db_master(user_id)}{suffix}'  # replica_


def redis_master(user_id: Optional[int] = None) -> int:
    if not user_id:
        return 0
    else:
        if user_id < 100001:
            return 0
        else:
            return int(user_id / 1000)


def datetime_to_unixtime(date_time) -> int:
    date_string = date_time.strftime('%Y-%m-%d %H:%M:%S')
    date_time = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=8)
    return int(time.mktime(date_time.timetuple()))


def unixtime_to_datetime(local_time):
    date_string = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(local_time))
    date_time = datetime.datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    return date_time


def unixtime_to_date(local_time):
    return time.strftime('%Y-%m-%d', time.localtime(local_time))


def datetime_timezone_zero():
    return datetime.datetime(timezone.now().year, timezone.now().month, timezone.now().day, 0, 0, 0)


def string_to_unixtime(string) -> int:
    date_time = datetime.datetime.strptime(string, '%Y-%m-%d %H:%M:%S')
    return int(time.mktime(date_time.timetuple()))
