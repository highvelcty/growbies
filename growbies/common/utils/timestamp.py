import time
from datetime import datetime, timezone
from typing import Optional, Union

UTC_Z = 'Z'

BASE_DT_FMT = '%Y-%m-%dT%H:%M:%S'

#: The timestamp string format.
FMT_DT = f'{BASE_DT_FMT}.%f{UTC_Z}'
FMT_DT_INT = f'{BASE_DT_FMT}{UTC_Z}'

PRECISION = 6

#: Return with precision 6 to match the datetime %f string formatter (6 decimal places)
#: See: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
TS_PRECISION_FMT = f'{{:.0{PRECISION}f}}'

TS_t = Union[str, datetime, int, float]


def get_elapsed_str(seconds: int) -> str:
    """
    Convert elapsed seconds into a human-friendly string:
    "W days, X hours, Y minutes, Z seconds"
    """

    if seconds < 0:
        raise ValueError("Elapsed time cannot be negative")

    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"


def get_unix_time(ts: Optional[TS_t] = None, fmt: str = FMT_DT) -> float:
    """
    :param ts: A timestamp that may take the following forms:
        - a string, matching the :data:`FMT` format.
        - an integer or a float, in which case it represents the number of seconds since the unix
          epoch.
        - A datetime object. This object will be made timezone aware and set to UTC prior to
            returning the number of seconds since the unix epoch.
            Warning: timezone offsets will be applied if the input datetime object is naive and
            created outside the UTC timezone OR is timezone aware and not set to UTC.
        - None. In which case a timestamp will be created.
    :param fmt: The string parsing format.

    :return: The number of seconds since the Unix epoch as a floating point value using the
        format given by :data:`TS_PRECISION_FMT`.
    """
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc).timestamp()
    elif isinstance(ts, (int, float, str)):
        try:
            return float(TS_PRECISION_FMT.format(float(ts)))
        except ValueError:
            try:
                return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc).timestamp()
            except ValueError:
                raise ValueError(f'Unable to convert "{ts}" to a UTC epoch timestamp.')
    else:
        return round(time.time(), PRECISION)


def get_utc_dt(ts: Optional[TS_t] = None, fmt: str = FMT_DT) -> datetime:
    """
    :param ts: A timestamp that may take the following forms:
        - a string, matching the :data:`FMT` format.
        - an integer or a float, in which case it represents the number of seconds since the unix
          epoch.
        - A datetime object. This object will be made timezone aware and set to UTC prior to
            returning the number of seconds since the unix epoch.
            Warning: timezone offsets will be applied if the input datetime object is naive and
            created outside the UTC timezone OR is timezone aware and not set to UTC.
        - None. In which case a timestamp will be created.
    :param fmt: The string parsing format.

    :return: A timezone aware UTC datetime.
    """
    if isinstance(ts, datetime):
        dt = ts.astimezone(timezone.utc)
    elif isinstance(ts, str):
        dt = datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
    elif isinstance(ts, (int, float)):
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    else:
        dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
    return dt


def get_utc_iso_ts_str(ts: Optional[TS_t] = None,
                       fmt: str = FMT_DT, timespec: str = 'microseconds') -> str:
    """
    :param ts: A timestamp that may take the following forms:
        - a string, matching the :data:`FMT` format.
        - an integer or a float, in which case it represents the number of seconds since the unix
          epoch.
        - A datetime object. This object will be made timezone aware and set to UTC prior to
            returning the number of seconds since the unix epoch.
            Warning: timezone offsets will be applied if the input datetime object is naive and
            created outside the UTC timezone OR is timezone aware and not set to UTC.
        - None. In which case a timestamp will be created.
    :param fmt: The string parsing format.
    :param timespec: The precision to format the string with.

    :return: A UTC timestamp string.
    """
    return get_utc_dt(ts, fmt).isoformat(timespec=timespec).split('+')[0] + UTC_Z


class ContextElapsedTime(object):
    def __init__(self):
        self._start_time = None
        self._end_time = None

    def __enter__(self):
        self._start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_time = datetime.now()

    def __str__(self):

        # Format the elapsed time
        if self._end_time is None:
            end_time = datetime.now()
        else:
            end_time = self._end_time

        if self._start_time is None:
            return 'Timer not started.'

        elapsed_time = end_time - self._start_time
        days = elapsed_time.days
        hours = elapsed_time.seconds // 3600
        minutes = (elapsed_time.seconds % 3600) // 60
        seconds = elapsed_time.seconds % 60
        microseconds = elapsed_time.microseconds

        return f'{days} days, {hours:02d}:{minutes:02d}:{seconds:02d}.{microseconds:06d}'
