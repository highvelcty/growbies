import atexit
import logging
import sys
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from growbies.utils import timestamp
from growbies.utils.paths import RepoPaths

class ThreadLocal(threading.local):
    def __init__(self, /, **kw):
        self.__dict__.update(kw)

        self.name = None
        self.set_name()

    def set_name(self, name: Optional[str] = None):
        if not name:
            name = threading.current_thread().name
        self.name = name

thread_local = ThreadLocal()

class ThreadNameFilter(logging.Filter):
    def filter(self, record):
        record.thread_name = thread_local.name
        return True

class StdoutFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self._level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return self._level <= record.levelno < logging.ERROR


#: This is the max number of bytes for each rotating file. e.g. If BACKUP_COUNT (zero
#: based numbering) is 2 and this is 10MiB, the maximum number of bytes that will be logged via
#: this handler.
MAX_BYTES = 1024 * 1024 * 25  # 25 MiB

#: This is the maximum number of rotations. It is a zero-based number. e.g. A setting of 2
#: would result in three log files: sdu.log, sdu.log.1 sdu.log.2
BACKUP_COUNT = 2


def start(path: Path, file_level: int = logging.DEBUG, stdout_level: int = logging.DEBUG) \
        -> logging.Logger:
    logger = logging.getLogger(RepoPaths.REPO_ROOT.value.resolve().name)
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(f'|%(asctime)s{timestamp.UTC_Z} '
                            f'%(thread_name)s '
                            f'%(levelname)s| '
                            f'%(message)s',
                            timestamp.BASE_DT_FMT)
    fmt.converter = time.gmtime


    file_hdlr = RotatingFileHandler(path, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
    file_hdlr.setLevel(file_level)
    file_hdlr.setFormatter(fmt)

    stdout_hdlr = logging.StreamHandler(stream=sys.stdout)
    stdout_hdlr.setLevel(stdout_level)
    stdout_hdlr.setFormatter(fmt)
    stdout_hdlr.addFilter(StdoutFilter(stdout_level))

    stderr_hdlr = logging.StreamHandler(stream=sys.stderr)
    stderr_hdlr.setLevel(logging.ERROR)
    stderr_hdlr.setFormatter(fmt)

    # Add the thread name filter to each handler so that each subsequent logger will have the
    # filter. If the filter is only added to the logger, only this particular instance of the
    # logger will have the filter
    file_hdlr.addFilter(ThreadNameFilter())
    stdout_hdlr.addFilter(ThreadNameFilter())
    stderr_hdlr.addFilter(ThreadNameFilter())

    logger.addHandler(file_hdlr)
    logger.addHandler(stdout_hdlr)
    logger.addHandler(stderr_hdlr)

    atexit.register(logging.shutdown)

    return logger

