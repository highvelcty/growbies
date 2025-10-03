from enum import Enum
from pathlib import Path
from typing import Iterable, Optional
import logging

from . import log
from growbies.cfg.cfg import Cfg
from growbies.db.engine import get_db_engine
from growbies.db.models.account import Account
from growbies.db.models.gateway import Gateway
from growbies.utils.paths import InstallPaths, RepoPaths
from growbies.utils import timestamp

logger = logging.getLogger(__name__)

class Session(object):
    TAG_DELIMITER = '-'
    DEFAULT_TAG = 'default'
    DEFAULT_OUTPUT = RepoPaths.OUTPUT.value.absolute()
    DIRECTORY_TIMESTAMP_FMT = timestamp.BASE_FMT + 'Z'

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
        log.start(RepoPaths.DEFAULT_LOG.value, file_level=logging.DEBUG, stdout_level=logging.DEBUG)
        logger.info(f'{session_type_str} session\n'
                    f'  path_to_data: {self.path_to_data}')

    @property
    def path_to_data(self) -> Path:
        return self._session_dir / self.OutputFiles.DATA.value

class Session2(object):
    def __init__(self):
        # Initialize logging
        log.start(InstallPaths.VAR_LOG_GROWBIES_LOG.value, file_level=logging.DEBUG,
                  stdout_level=logging.DEBUG)
        logger.info(f'Session start')

        # Load configuration from file.
        self._cfg = Cfg()
        self._cfg.load()

        # Update the DB with account and gateway information input via configuration.
        db_engine = get_db_engine()
        cfg_account = Account(**self._cfg.account.model_dump())
        db_accounts = db_engine.account.get_multi(cfg_account.name)
        if db_accounts:
            self._account = db_accounts[0]
        else:
            self._account = db_engine.account.upsert(cfg_account)

        cfg_gateway = Gateway(name=self._cfg.gateway.name, account=self._account.id)
        db_gateways = db_engine.gateway.get_multi(cfg_gateway.name)
        if db_gateways:
            self._gateway = db_gateways[0]
        else:
            self._gateway = db_engine.gateway.upsert(cfg_gateway)

    @property
    def account(self) -> Account:
        return self._account

    @property
    def gateway(self) -> Gateway:
        return self._gateway

session = None
def get_session() -> Session2:
    global session
    if session is None:
        session = Session2()
    return session
