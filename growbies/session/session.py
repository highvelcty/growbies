from dataclasses import asdict
import logging

from . import log
from growbies.cfg.cfg import get_cfg
from growbies.db.engine import get_db_engine
from growbies.db.models.account import Account
from growbies.db.models.gateway import Gateway
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)

class Session(object):
    def __init__(self):
        # Initialize logging
        log.start(InstallPaths.VAR_LOG_GROWBIES_LOG.value, file_level=logging.DEBUG,
                  stdout_level=logging.DEBUG)
        logger.info(f'Session start')

        # Load configuration from file.
        self._cfg = get_cfg()

        # Update the DB with account and gateway information input via configuration.
        db_engine = get_db_engine()
        cfg_account = Account(**asdict(self._cfg.account))
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
def get_session() -> Session:
    global session
    if session is None:
        session = Session()
    return session
