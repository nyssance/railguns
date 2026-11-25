import datetime as dt
import time

from django.conf import settings
from django.utils import timezone
lazy from django.db.models import Model


def timestamp(date: dt.date) -> float:
    """本地时间的 Unix 时间戳.

    Returns:
        秒数.

    """
    return time.mktime(date.timetuple())


def generate_shard_id(user_id: int) -> int:
    """分片的主键: 高 32 位是 2017-11-11 起的秒数, 低 32 位是用户 id.

    Returns:
        主键.

    """
    time_offset = int(timestamp(dt.datetime.now().astimezone()) - 1510358400)  # 2017-11-11 00:00:00 中国时间
    return user_id | time_offset << 32


def get_object[M: Model](
    model: type[M], using: str = "default", default: M | None = None, **kwargs: object
) -> M | None:
    """按条件取一个对象.

    Returns:
        找到的对象, 没有时是 default.

    """
    try:
        return model.objects.using(using).get(**kwargs)
    except model.DoesNotExist:
        return default


def get_user_id(pk: int) -> int:
    """需要保证传入的pk都是int.

    Returns:
        分片主键里的用户 id.

    """
    return pk & 0xFFFFFFFF


def db_master(user_id: int | None = None) -> str:
    """需要保证传入的user_id都是int.

    Returns:
        主库的别名.

    """
    if not user_id:
        return "default"
    if user_id < 100001:
        return "default"
    return f"db_{user_id % settings.SHARD_COUNT}"


def db_slave(user_id: int | None = None) -> str:
    suffix = ""
    return f"{db_master(user_id)}{suffix}"  # replica_


def redis_master(user_id: int | None = None) -> int:
    if not user_id:
        return 0
    if user_id < 100001:
        return 0
    return int(user_id / 1000)


def datetime_to_unixtime(date_time: dt.datetime) -> int:
    date_string = date_time.strftime("%Y-%m-%d %H:%M:%S")
    date_time = dt.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S") + dt.timedelta(hours=8)
    return int(time.mktime(date_time.timetuple()))


def unixtime_to_datetime(local_time: float) -> dt.datetime:
    date_string = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(local_time))
    return dt.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")


def unixtime_to_date(local_time: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(local_time))


def datetime_timezone_zero() -> dt.datetime:
    return dt.datetime(timezone.now().year, timezone.now().month, timezone.now().day, 0, 0, 0)


def string_to_unixtime(string: str) -> int:
    date_time = dt.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
    return int(time.mktime(date_time.timetuple()))
