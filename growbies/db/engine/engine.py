from contextlib import contextmanager
import logging
from typing import Any, Generator

from sqlmodel import create_engine, Session, SQLModel


from .account import AccountEngine
from .device import DevicesEngine
from .gateway import GatewayEngine
from growbies.db.constants import SQLMODEL_LOCAL_ADDRESS

logger = logging.getLogger(__name__)


class DBEngine:
    def __init__(self):
        self._lazy_init_engine = None
        self.account = AccountEngine(self)
        self.gateway = GatewayEngine(self)
        self.devices = DevicesEngine(self)

    @property
    def _engine(self):
        if self._lazy_init_engine is None:
            # echo_pool and echo can be set to "debug" for more details.
            self._lazy_init_engine = create_engine(SQLMODEL_LOCAL_ADDRESS, echo_pool=False,
                                                   echo=False)

        return self._lazy_init_engine

    def init_tables(self):
        # All models representing tables found in the import space will be created.
        # noinspection PyUnresolvedReferences
        from growbies.db.models import addressing
        with Session(self._engine) as session:
            SQLModel.metadata.create_all(self._engine)
            session.commit()
            session.close()

    def _merge(self, thing):
        with self.new_session() as session:
            merged = session.merge(thing)
            session.commit()
            # To make dynamically created (such as id fields) accessible after session close
            # (detachment)
            session.refresh(merged)
            return merged

    @contextmanager
    def new_session(self) -> Generator[Session, Any, None]:
        session = Session(self._engine)
        try:
            yield session
        finally:
            session.close()


# Application global singleton.
_db_engine = None
def get_db_engine():
    """Return the application global singleton, initializing it if it has not yet been."""
    global _db_engine
    if _db_engine is None:
        _db_engine = DBEngine()
    return _db_engine
