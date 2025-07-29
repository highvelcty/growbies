from enum import Enum
from pathlib import Path
from typing import Iterable, Optional
import logging

from . import log
from growbies.utils.paths import RepoPaths
from growbies.utils import timestamp

logger = logging.getLogger(__name__)

class Session(object):
    TAG_DELIMITER = '-'
    DEFAULT_TAG = 'default'
    DEFAULT_OUTPUT = RepoPaths.OUTPUT.value.absolute()
    DIRECTORY_TIMESTAMP_FMT = BASE_FMT = '%Y-%m-%dT%H%M%SZ'

    class OutputFiles(Enum):
        LOG = RepoPaths.DEFAULT_LOG.value.name
        DATA = RepoPaths.DEFAULT_DATA.value.name

    def __init__(self, output: Optional[Path|str] = DEFAULT_OUTPUT,
                 tags: Optional[Iterable[str]] = None):

        session_type_str = 'New'

        if output is None:
            self._output_dir = RepoPaths.OUTPUT.value
        else:
            self._output_dir = Path(output)

        self._session_dir = None

        if tags is not None:
            # Search for an existing output subdirectory
            for discovered_path in self._output_dir.iterdir():
                # If all tags given are found in the path name, an existing subdirectory exists
                for tag in tags:
                    if tag not in discovered_path.name:
                        # This existing path does not have all the tags
                        break
                else:
                    # All tags were found in the path. Set the output directory to the discovered
                    # path and quit searching.
                    session_type_str = 'Existing'
                    self._session_dir = discovered_path
                    break

        if self._session_dir is None:
            # An existing subdirectory was not found. Create one.
            dt = timestamp.get_utc_dt()
            session_name = dt.strftime(self.DIRECTORY_TIMESTAMP_FMT)
            if tags:
                session_name += self.TAG_DELIMITER + self.TAG_DELIMITER.join(tags)
            else:
                session_name += self.TAG_DELIMITER + self.DEFAULT_TAG

            self._session_dir = self._output_dir / session_name

        self._session_dir.mkdir(parents=True, exist_ok=True)
        log.start(RepoPaths.DEFAULT_LOG.value, file_level=logging.DEBUG, stdout_level=logging.INFO)
        logger.info(f'{session_type_str} session\n'
                    f'  path_to_data: {self.path_to_data}')

    @property
    def path_to_data(self) -> Path:
        return self._session_dir / self.OutputFiles.DATA.value
