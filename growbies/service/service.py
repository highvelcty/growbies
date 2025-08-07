from typing import TypeVar
import logging
import os
import pickle
import time

from . import Op
from growbies.utils.filelock import FileLock
from growbies.session import Session2
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)



class CmdHdr(object):
    _op: Op = None

    @property
    def op(self) -> Op:
        return self._op


class BaseCmd(CmdHdr):
    pass
TBaseCmd = TypeVar('TBaseCmd', bound=BaseCmd)


class StopCmd(BaseCmd):
    _op = Op.STOP


class Queue(object):
    PATH = InstallPaths.VAR_LIB_GROWBIES_LOCK_Q.value
    QUEUE_POLLING_INTERVAL_SEC = 0.25

    def __init__(self):
        self.PATH.touch(exist_ok=True)
        self._cached_mtime = 0

    def flush(self):
        with FileLock(self.PATH, 'w'):
            pass

    def get(self) -> list[TBaseCmd]:
        contents = list()
        while True:
            current_mtime = os.stat(self.PATH).st_mtime
            if self._cached_mtime == current_mtime:
                time.sleep(self.QUEUE_POLLING_INTERVAL_SEC)
            else:
                with FileLock(self.PATH, 'ab+') as file:
                    file.seek(0)
                    try:
                        contents: list[TBaseCmd] = pickle.load(file)
                    except EOFError:
                        pass
                    file.clear()

                self._cached_mtime = os.stat(self.PATH).st_mtime
                break

        return contents

    def put(self, item: TBaseCmd):
        contents = list()
        with FileLock(self.PATH, 'ab+') as file:
            file.seek(0)
            try:
                contents: list[TBaseCmd] = pickle.load(file)
            except EOFError:
                pass
            contents.append(item)
            file.clear()
            pickle.dump(contents, file)

class Service:
    def __init__(self):
        self._queue = Queue()
        self._session = Session2()

    def run(self):
        done = False
        try:
            while not done:
                for cmd in self._queue.get():
                    if cmd.op == Op.STOP:
                        done = True
                        break
                    else:
                        logger.error(f'Unknown command {cmd} received.')
        except KeyboardInterrupt:
            self._queue.put(StopCmd())
            return self.run()
