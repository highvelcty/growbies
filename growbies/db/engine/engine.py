from contextlib import contextmanager
import logging

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
            self._lazy_init_engine = create_engine(SQLMODEL_LOCAL_ADDRESS, echo_pool=True,
                                                   echo=True)
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
    def new_session(self) -> Session:
        session = Session(self._engine)
        try:
            yield session
        finally:
            session.close()



# Application global singleton
db_engine = None
def get_db_engine():
    global db_engine
    if db_engine is None:
        db_engine = DBEngine()
    return db_engine
