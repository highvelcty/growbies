from enum import Enum
from pathlib import Path
from typing import Iterable, Optional, Union
import logging

from . import log
from growbies.utils.paths import Paths
from growbies.utils import timestamp

class Session(object):
    TAG_DELIMITER = '-'
    DEFAULT_DIRECTORY = Path('default')
    DIRECTORY_TIMESTAMP_FMT = BASE_FMT = '%Y-%m-%dT%H%M%SZ'

    class OutputFiles(Enum):
        LOG = Paths.DEFAULT_LOG.value.name
        DATA = Paths.DEFAULT_DATA.value.name

    def __init__(self, path_or_tags: Optional[Union[Union[Path, str], Iterable[str]]] = None):
        """
        :param path_or_tags: A value of::
            - None: Continue the default session in the default subdirectory in the output
              directory.
            - Empty list: Start a session at an ISO timestamp subdirectory in the output
              directory.
            - Path that exists: Continue a session at the existing path.
            - Path that does not exist: Start a session associated with the new path.
        """
        if isinstance(path_or_tags, (Path, str)):
            self._output_dir = Path(path_or_tags)
        elif path_or_tags is None:
            self._output_dir = Paths.DEFAULT_OUTPUT_DIR.value
        else:
            dt = timestamp.get_utc_dt()
            dir_name = dt.strftime(self.DIRECTORY_TIMESTAMP_FMT)
            if path_or_tags:
                dir_name += self.TAG_DELIMITER + self.TAG_DELIMITER.join(path_or_tags)

            self._output_dir = Paths.OUTPUT.value / dir_name

        self._output_dir.mkdir(parents=True, exist_ok=True)
        log.start(Paths.DEFAULT_LOG.value, file_level=logging.DEBUG, stdout_level=logging.INFO)

    @property
    def path_to_data(self) -> Path:
        return self._output_dir / self.OutputFiles.DATA.value
