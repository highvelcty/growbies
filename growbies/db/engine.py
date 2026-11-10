
from contextlib import contextmanager
import logging
from typing import Any, Generator

from sqlalchemy import Engine
from sqlmodel import create_engine, Session, SQLModel

from .models import account, gateway, device, datapoint, link, project, session, tag, tare, user
from growbies.constants import SQLMODEL_ADDRESS_FMT
from growbies.cfg import get_cfg

logger = logging.getLogger(__name__)

class DBEngine:
    def __init__(self):
        self._engine = self._create_engine()
        self._init_tables()

        self.account = account.AccountEngine(self)
        self.datapoint = datapoint.DataPointEngine(self)
        self.gateway = gateway.GatewayEngine(self)
        self.device = device.DeviceEngine(self)
        self.project = project.ProjectEngine(self)
        self.session = session.SessionEngine(self)
        self.tag = tag.TagEngine(self)
        self.tare = tare.TareEngine(self)
        self.user = user.UserEngine(self)
        self.link = link.LinkEngine(self)

    @staticmethod
    def _create_engine() -> Engine:
        cfg = get_cfg()
        address = SQLMODEL_ADDRESS_FMT.format(address=cfg.database.address)

        return create_engine(
            address,
            echo=False,
            echo_pool=False,

            # Connection pool health and lifecycle.
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_timeout=30,

            # PostgreSQL / psycopg2 connection settings.
            connect_args={
                'connect_timeout': 10,
                'application_name': 'growbies-db-access',
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 3,
            },
        )

    def _init_tables(self):
        # All table models found in the import space at this point will be created.
        with Session(self._engine) as sess:
            SQLModel.metadata.create_all(self._engine)
            sess.commit()

    @contextmanager
    def new_session(self) -> Generator[Session, Any, None]:
        with Session(self._engine) as sess:
            yield sess

# Application global singleton.
_db_engine = None

def get_db_engine():
    """Return the application global singleton, initializing it if it has not yet been."""
    global _db_engine
    if _db_engine is None:
        _db_engine = DBEngine()
    return _db_engine
