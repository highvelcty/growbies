from contextlib import contextmanager

from sqlmodel import create_engine, Session, SQLModel

from .constants import SQLMODEL_LOCAL_ADDRESS
from .models.addressing import Account, Gateway

class Engine:
    def __init__(self):
        self._lazy_init_engine = None

    @property
    def _engine(self):
        if self._lazy_init_engine is None:
            self._lazy_init_engine = create_engine(SQLMODEL_LOCAL_ADDRESS, echo_pool=True,
                                                   echo=True)
        return self._lazy_init_engine

    def init_tables(self):
        # All models representing tables found in the import space will be created.
        from . import models
        with Session(self._engine) as session:
            SQLModel.metadata.create_all(self._engine)
            session.commit()
            session.close()

    def _merge(self, thing):
        with self._new_session() as session:
            merged = session.merge(thing)
            session.commit()
            # To make dynamically created (such as id fields) accessible after session close
            # (detachment)
            session.refresh(merged)
            return merged

    def merge_gateway(self, gateway: Gateway) -> Gateway:
        return self._merge(gateway)

    @contextmanager
    def _new_session(self):
        session = Session(self._engine)
        try:
            yield session
        finally:
            session.close()

# Application global singleton
db_engine = Engine()