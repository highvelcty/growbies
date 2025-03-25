from pathlib import Path
import fcntl


class FileLock(object):
    def __init__(self, path: Path, mode: str):
        self._path = path
        self._mode = mode
        self._fd = None

    def __enter__(self):
        self._fd = open(self._path, self._mode)
        fcntl.lockf(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return self._fd

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.lockf(self._fd.fileno(), fcntl.LOCK_UN)
        self._fd.close()