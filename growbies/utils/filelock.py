from pathlib import Path
import fcntl

from growbies.utils.paths import Paths


class FileLock(object):
    def __init__(self, path: Path = Paths.FILELOCK.value):
        self._path = path
        self._fd = None

    def __enter__(self):
        self._fd = open(self._path, 'w')
        fcntl.lockf(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.lockf(self._fd, fcntl.LOCK_UN)
        self._fd.close()