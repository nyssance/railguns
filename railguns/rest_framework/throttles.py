from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class OncePerDayUserThrottle(UserRateThrottle):
    rate = '10/day'


class OncePerDayAnnoThrottle(AnonRateThrottle):
    rate = '10/day'


class UploadPerMinUserThrottle(UserRateThrottle):
    rate = '200/min'


class UploadPerMinAnnoThrottle(AnonRateThrottle):
    rate = '2000/min'
