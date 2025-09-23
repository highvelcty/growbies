from contextlib import contextmanager
import logging
from typing import Any, Generator

from sqlmodel import create_engine, Session, SQLModel

from .models.account import AccountEngine
from .models.device import DevicesEngine
from .models.gateway import GatewayEngine
from .models.tare import TareEngine
from .models.datapoint import DataPointEngine
from growbies.constants import SQLMODEL_LOCAL_ADDRESS

logger = logging.getLogger(__name__)

# All models representing tables found in the import space will be created, but the static
# checker doesn't know this.
# noinspection PyUnresolvedReferences
from growbies.db.models import account, gateway, device, datapoint, session, tag, user

class DBEngine:
    def __init__(self):
        self._lazy_init_engine = None
        self.account = AccountEngine(self)
        self.gateway = GatewayEngine(self)
        self.devices = DevicesEngine(self)
        self.tare = TareEngine(self)
        self.datapoint = DataPointEngine(self)

    @property
    def _engine(self):
        if self._lazy_init_engine is None:
            # echo_pool and echo can be set to "debug" for more details.
            self._lazy_init_engine = create_engine(SQLMODEL_LOCAL_ADDRESS, echo_pool=False,
                                                   echo=False)

        return self._lazy_init_engine

    def init_tables(self):
        with Session(self._engine) as sess:
            SQLModel.metadata.create_all(self._engine)
            sess.commit()
            sess.close()

    def _merge(self, thing):
        with self.new_session() as sess:
            merged = sess.merge(thing)
            sess.commit()
            # To make dynamically created (such as id fields) accessible after session close
            # (detachment)
            sess.refresh(merged)
            return merged

    @contextmanager
    def new_session(self) -> Generator[Session, Any, None]:
        sess = Session(self._engine)
        try:
            yield sess
        finally:
            sess.close()


# Application global singleton.
_db_engine = None
def get_db_engine():
    """Return the application global singleton, initializing it if it has not yet been."""
    global _db_engine
    if _db_engine is None:
        _db_engine = DBEngine()
    return _db_engine
