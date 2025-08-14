from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, cast, Generator, Iterator, Optional
import atexit
import logging
import os
import pickle
import time

from inotify_simple import INotify, flags

from growbies.models.service import TBaseCmd
from growbies.utils.filelock import FileLock
from growbies.utils.paths import InstallPaths
from growbies.utils.types import Pickleable_t

logger = logging.getLogger(__name__)


class Queue:
    BLOCKING_IO_ERROR_RETRIES = 5
    BLOCKING_IO_ERROR_DELAY_SEC = 0.01
    DEFAULT_GET_TIMEOUT_SEC = 10
    DEFAULT_POLLING_INTERVAL_SEC = 0.01
    def __init__(self,
                 path: Path,
                 polling_interval_sec: float = DEFAULT_POLLING_INTERVAL_SEC):

        self._path = Path(path)
        self._polling_interval_sec = polling_interval_sec

        # Initialize path
        self._path.touch(exist_ok=True)
        self._inotify = INotify()
        self._inotify_watch = None

        self._cached_mtime = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _read_contents(self) -> list[Pickleable_t]:
        contents = list()

        with self._file_lock() as file:
            file.seek(0)
            try:
                contents = pickle.load(cast(BinaryIO, file))
            except EOFError:
                pass

            if contents:
                file.clear()
            else:
                if not self._inotify_watch:
                    self._inotify_watch = self._inotify.add_watch(self._path, flags.CLOSE_WRITE)

        return contents

    def get(self, timeout: int = DEFAULT_GET_TIMEOUT_SEC) -> Iterator[Pickleable_t]:
        contents = self._read_contents()
        if not contents:
            events = list()
            startt = time.time()
            # Comparing to length 2 because the first event will be from closing the file handle
            # from the read. The read has to have write permissions to obtain the file lock.
            while len(events) < 2:
                timeout_remaining = timeout - (time.time() - startt)
                if timeout_remaining < 0:
                    break
                events.extend(self._inotify.read(timeout=int(timeout_remaining) * 1000))

            if events:
                contents = self._read_contents()

        yield from contents

    def put(self, item: Pickleable_t):
        contents = list()
        with self._file_lock() as file:
            file.seek(0)
            try:
                contents = pickle.load(cast(BinaryIO, file))
            except EOFError:
                pass
            contents.append(item)
            file.clear()
            # noinspection PyTypeChecker
            pickle.dump(contents, file)

    @contextmanager
    def _file_lock(self) -> Generator[FileLock, None, None]:
        """Context manager for opening a file with retries on BlockingIOError."""
        last_exc: Exception | None = None

        for _ in range(self.BLOCKING_IO_ERROR_RETRIES):
            try:
                with FileLock(self._path, 'ab+') as file:
                    yield file
                return
            except BlockingIOError as e:
                last_exc = e
                time.sleep(self.BLOCKING_IO_ERROR_DELAY_SEC)

        # if we exhausted all retries, propagate the last exception
        if last_exc is not None:
            raise last_exc


class PidQueue(Queue):
    def __init__(self, pid: Optional[int] = None):
        # If pid is None, the file is being created from new. Cleanup with be automated. Else,
        # if pid is not None, cleanup will not be automated as the object will be attaching to an
        # existing file instead of creating from new. It is the responsibility of the creator to
        # clean up.
        if pid is None:
            pid = os.getpid()
            self._auto_cleanup = True
        else:
            self._auto_cleanup = False

        self._path = InstallPaths.RUN_GROWBIES.value / f'{pid}_resp_queue.pkl'
        super().__init__(self._path)

        if self._auto_cleanup:
            atexit.register(self._cleanup)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._auto_cleanup:
            self._cleanup()

    def _cleanup(self):
        try:
            os.remove(self._path)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Warning: failed to remove {self._path} at exit: {e}")

class ServiceQueue(Queue):
    PATH = InstallPaths.RUN_GROWBIES_CMD_Q.value

    def __init__(self):
        super().__init__(self.PATH)
        self._pid = os.getpid()

    def get(self, *args) -> Iterator[TBaseCmd]:
        yield from super().get()

    def put(self, cmd: TBaseCmd):
        cmd.qid = self._pid
        return super().put(cmd)
