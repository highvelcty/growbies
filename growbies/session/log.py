import atexit
import logging
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from growbies.utils import timestamp
from growbies.utils.paths import Paths


class StdoutFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self._level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self._level


class LineFmt(logging.Formatter):
    def __init__(self):
        super().__init__(f'|%(asctime)s{timestamp.UTC_Z} '
                            f'%(name)s '
                            f'%(levelname)s|\n'
                            f'%(message)s',
                            timestamp.BASE_FMT)


class CustomRotatingFileHandler(RotatingFileHandler):
    NAME = 'base_rotating_file_handler'
    LEVEL = logging.NOTSET

    #: This is the max number of bytes for each rotating file. e.g. If BACKUP_COUNT (zero
    #: based numbering) is 2 and this is 10MiB, the maximum number of bytes that will be logged via
    #: this handler.
    MAX_BYTES = 1024 * 1024 * 25  # 25 MiB

    #: This is the maximum number of rotations. It is a zero-based number. e.g. A setting of 2
    #: would result in three log files: sdu.log, sdu.log.1 sdu.log.2
    BACKUP_COUNT = 2

    def __init__(self, filename: Path):
        super().__init__(filename, maxBytes=self.MAX_BYTES, backupCount=self.BACKUP_COUNT)
        self.setFormatter(LineFmt())



def start(path: Path, file_level: int = logging.DEBUG, stdout_level: int = logging.DEBUG) \
        -> logging.Logger:
    logger = logging.getLogger(Paths.ROOT.value.resolve().name)
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(f'|%(asctime)s{timestamp.UTC_Z} '
                            f'%(name)s '
                            f'%(levelname)s|\n'
                            f'%(message)s',
                            timestamp.BASE_FMT)
    fmt.converter = time.gmtime

    # file_hdlr = logging.FileHandler(path)
    file_hdlr = CustomRotatingFileHandler(path)
    file_hdlr.setLevel(file_level)
    file_hdlr.setFormatter(fmt)

    stdout_hdlr = logging.StreamHandler(stream=sys.stdout)
    stdout_hdlr.setLevel(stdout_level)
    stdout_hdlr.setFormatter(fmt)
    stdout_hdlr.addFilter(StdoutFilter(stdout_level))

    stderr_hdlr = logging.StreamHandler(stream=sys.stderr)
    stderr_hdlr.setLevel(logging.ERROR)
    stderr_hdlr.setFormatter(fmt)

    logger.addHandler(file_hdlr)
    logger.addHandler(stdout_hdlr)
    logger.addHandler(stderr_hdlr)

    atexit.register(logging.shutdown)

    return logger
