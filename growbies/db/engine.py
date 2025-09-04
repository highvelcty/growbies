from contextlib import contextmanager
import logging
from typing import Any, Generator

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import create_engine, Session, SQLModel


from .account import AccountEngine
from .device import DevicesEngine
from .gateway import GatewayEngine
from growbies.db.constants import SQLMODEL_LOCAL_ADDRESS

# All models representing tables found in the import space will be created, but the static
# checker doesn't know this.
# noinspection PyUnresolvedReferences
from growbies.db.models import addressing
from growbies.db.models.endpoint_types import EndpointTypes

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
        with Session(self._engine) as session:
            SQLModel.metadata.create_all(self._engine)
            session.commit()
            session.close()

    def _init_endpoint_type_table(self):
        default_endpoint_types = [
            {EndpointTypes.Key.NAME: 'mass',
             EndpointTypes.Key.DESCRIPTION: 'Weight measured in DAC.'},
            {EndpointTypes.Key.NAME: 'temperature',
             EndpointTypes.Key.DESCRIPTION: 'Temperature measured in DAC.'}
        ]

        with Session(self._engine) as session:
            for row in default_endpoint_types:
                # The postgres sqlalchemy insert is used here because it supports on conflict do
                # nothing. Whereas, the native sqlmodel `add` statement does not.
                stmt = insert(EndpointTypes).values(**row).on_conflict_do_nothing(
                    index_elements=["name"]  # ensures unique name prevents duplicates
                )
                # noinspection PyTypeChecker
                session.exec(stmt)
            session.commit()

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
