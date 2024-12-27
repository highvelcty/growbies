from enum import Enum
from pathlib import Path
from typing import Iterable, Optional, Union
import logging

from . import log
from precision_farming.utils.paths import Paths
from precision_farming.utils import timestamp

class Session(object):
    TAG_DELIMITER = '-'
    DEFAULT_DIRECTORY = Path('default')

    class OutputFiles(Enum):
        LOG = 'log.log'
        DATA = 'data.csv'

    def __init__(self, path_or_tags: Optional[Union[Path, Iterable[str]]] = None):
        if isinstance(path_or_tags, Path):
            self._output_dir = path_or_tags
        elif path_or_tags is None:
            self._output_dir = Paths.OUTPUT.value / self.DEFAULT_DIRECTORY
        else:
            if path_or_tags:
                dir_name = (timestamp.get_utc_iso_ts_str() + '-' +
                            self.TAG_DELIMITER.join(path_or_tags))
            else:
                dir_name = timestamp.get_utc_iso_ts_str()

            self._output_dir = Paths.OUTPUT.value / dir_name
            self._output_dir.mkdir()

        log.start(self._path_to_log, file_level=logging.INFO, stdout_level=logging.INFO)

    @property
    def _path_to_log(self) -> Path:
        return self._output_dir / self.OutputFiles.LOG.value

    @property
    def path_to_data(self) -> Path:
        return self._output_dir / self.OutputFiles.DATA.value
