from fcntl import flock, LOCK_EX
from typing import TypeVar
import logging
import os
import pickle
import time

from . import Cmd
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)


class CmdHdr(object):
    _cmd: Cmd = None

    @property
    def cmd(self) -> Cmd:
        return self._cmd


class BaseCmd(CmdHdr):
    pass
TBaseCmd = TypeVar('TBaseCmd', bound=BaseCmd)


class StopCmd(BaseCmd):
    _cmd = Cmd.STOP


class Queue(object):
    PATH = InstallPaths.VAR_LIB_GROWBIES_LOCK_Q.value
    QUEUE_POLLING_INTERVAL_SEC = 0.25

    def __init__(self):
        self.PATH.touch(exist_ok=True)
        self._cached_mtime = 0

    def put(self, item: TBaseCmd):
        with open(self.PATH, 'w+') as file:
            with flock(file.fileno(), LOCK_EX):
                # noinspection PyTypeChecker
                contents: list[TBaseCmd] = pickle.load(file)
                contents.append(item)
                file.seek(0)
                file.truncate()
                # noinspection PyTypeChecker
                pickle.dump(contents, file)

    def get(self) -> list[TBaseCmd]:
        while True:
            current_mtime = os.stat(self.PATH).st_mtime
            if self._cached_mtime == current_mtime:
                time.sleep(self.QUEUE_POLLING_INTERVAL_SEC)
            else:
                with open(self.PATH, 'r') as file:
                    # noinspection PyTypeChecker
                    contents: list[TBaseCmd] = pickle.load(file)
                if contents:
                    return contents


def main():
    queue = Queue()
    while True:
        cmd = queue.get()

        if cmd == Cmd.STOP:
            break
        else:
            logger.error(f'Unknown command {cmd} received.')
