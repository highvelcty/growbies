from pathlib import Path
from typing import Any, Optional
import atexit
import os
import pickle
import time

from growbies.models.service import TBaseCmd
from growbies.utils.filelock import FileLock
from growbies.utils.paths import InstallPaths

PickleableType = Any

class Queue:
    DEFAULT_POLLING_INTERVAL_SEC = 0.25
    def __init__(self,
                 path: Path,
                 polling_interval_sec: float = DEFAULT_POLLING_INTERVAL_SEC):
        self._path = Path(path)
        self._polling_interval_sec = polling_interval_sec
        self._cached_mtime = 0
        self._path.touch(exist_ok=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def flush(self):
        with FileLock(self._path, 'w'):
            pass

    def get(self, block: bool = True) -> list[PickleableType]:
        contents = list()
        while True:
            current_mtime = os.stat(self._path).st_mtime
            if block and (self._cached_mtime == current_mtime):
                time.sleep(self._polling_interval_sec)
            else:
                with FileLock(self._path, 'ab+') as file:
                    file.seek(0)
                    try:
                        contents = pickle.load(file)
                    except EOFError:
                        pass
                    file.clear()

                self._cached_mtime = os.stat(self._path).st_mtime
                if contents:
                    break
            if not block:
                break

        return contents

    def put(self, item: PickleableType):
        contents = list()
        with FileLock(self._path, 'ab+') as file:
            file.seek(0)
            try:
                contents: pickle.load(file)
            except EOFError:
                pass
            contents.append(item)
            file.clear()
            pickle.dump(contents, file)

class PidQueue(Queue):
    def __init__(self, pid: Optional[int] = None):
        if pid is None:
            pid = os.getpid()
        self._path = InstallPaths.RUN_GROWBIES.value / f'{pid}_resp_queue.pkl'
        super().__init__(self._path)
        atexit.register(self._cleanup)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()

    def _cleanup(self):
        try:
            os.remove(self._path)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Warning: failed to remove {self._path} at exit: {e}")


class ServiceQueue(Queue):
    PATH = InstallPaths.RUN_GROWBIES.value

    def __init__(self):
        super().__init__(self.PATH)
        self._pid = os.getpid()

    def get(self, *args) -> list[TBaseCmd]:
        return super().get()

    def put(self, cmd: TBaseCmd):
        cmd.qid = self._pid
        return super().put(cmd)