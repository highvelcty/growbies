from sqlmodel import create_engine, Session, SQLModel

from .constants import SQLMODEL_LOCAL_ADDRESS

class DBIntf(object):
    def __init__(self):
        self._engine = create_engine(SQLMODEL_LOCAL_ADDRESS, echo_pool=True)

        SQLModel.metadata.create_all(self._engine)

class TableIntf(DBIntf):
    def __init__(self):
        super().__init__()

        self._session = None

    def __enter__(self):
        self._session = Session(self._engine)
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.commit()
