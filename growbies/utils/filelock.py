from pathlib import Path
from typing import AnyStr
import fcntl
import os


class FileLock(object):
    def __init__(self, path: Path, mode: str):
        self._path = path
        self._mode = mode
        self._fd = None
        self._fd = open(self._path, self._mode)

    def __enter__(self):
        fcntl.lockf(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        fcntl.lockf(self._fd.fileno(), fcntl.LOCK_UN)
        self._fd.close()

    def __getattr__(self, name):
        """
        Delegate attribute access to the wrapped object.
        """
        return getattr(self._fd, name)


    def clear(self):
        """
        Clear contents of file and reset index to zero.
        """
        self._fd.seek(0)
        self._fd.truncate()

class PidFileLock(FileLock):
    def __enter__(self):
        fd = super().__enter__()
        fd.clear()
        pid_str = str(os.getpid())
        pid_str = pid_str.encode() if 'b' in self._mode else pid_str
        fd.write(pid_str)
        fd.flush()
        return fd

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fd.seek(0)
        self._fd.truncate()
        super().__exit__(exc_type, exc_val, exc_tb)

    def get_pid(self) -> int:
        self._fd.seek(0)
        return int(self._fd.read())