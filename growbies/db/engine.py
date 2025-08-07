from .constants import SQLMODEL_LOCAL_ADDRESS

from sqlmodel import create_engine, Session, SQLModel

class Engine:
    def __init__(self):
        self._lazy_init_engine = None

    @property
    def _engine(self):
        if self._lazy_init_engine is None:
            self._lazy_init_engine = create_engine(SQLMODEL_LOCAL_ADDRESS, echo_pool=True)
        return self._lazy_init_engine

    def create_tables(self):
        with Session(self._engine):
            SQLModel.metadata.create_all(self._engine)

# Application global singleton
db_engine = Engine()