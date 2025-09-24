from contextlib import contextmanager
import logging
from typing import Any, Generator

from sqlalchemy import Engine
from sqlmodel import create_engine, Session, SQLModel

from .models import account, gateway, device, datapoint, session, tag, tare, user
from growbies.constants import SQLMODEL_LOCAL_ADDRESS

logger = logging.getLogger(__name__)

class DBEngine:
    def __init__(self):
        self._engine = self._create_engine()
        self._init_tables()

        self.account = account.AccountEngine(self)
        self.datapoint = datapoint.DataPointEngine(self)
        self.gateway = gateway.GatewayEngine(self)
        self.devices = device.DevicesEngine(self)
        self.session = session.SessionEngine(self)
        self.tag = tag.TagEngine(self)
        self.tare = tare.TareEngine(self)
        self.user = user.UserEngine(self)

    @staticmethod
    def _create_engine() -> Engine:
        return create_engine(SQLMODEL_LOCAL_ADDRESS, echo=False, echo_pool=False)


    def _init_tables(self):
        # All table models found in the import space at this point will be created.
        with Session(self._engine) as sess:
            SQLModel.metadata.create_all(self._engine)
            sess.commit()
            sess.close()

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
