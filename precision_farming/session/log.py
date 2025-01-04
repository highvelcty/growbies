import atexit
import logging
import sys
import time
from pathlib import Path

from precision_farming.utils import timestamp
from precision_farming.utils.paths import Paths


class StdoutFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self._level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self._level


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

    file_hdlr = logging.FileHandler(path)
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
