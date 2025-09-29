from datetime import datetime
from enum import StrEnum
from typing import Iterator, Optional, TYPE_CHECKING
import textwrap
import uuid

from prettytable import PrettyTable
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, SQLModel, Field, Relationship

from .common import BaseTableEngine
from .links import (SessionDataPointLink, SessionDeviceLink, SessionProjectLink, SessionTagLink,
                    SessionUserLink)
from growbies.constants import TABLE_COLUMN_WIDTH
from growbies.utils.timestamp import get_utc_dt
from growbies.utils.types import SessionID_t

if TYPE_CHECKING:
    from .datapoint import DataPoint
    from .device import Device
    from .project import Project
    from .tag import Tag
    from .user import User

class Session(SQLModel, table=True):
    class Key(StrEnum):
        ID = 'id'
        NAME = 'name'
        ACTIVE = 'active'
        DESCRIPTION = 'description'
        CREATED_AT = 'created_at'
        UPDATED_AT = 'updated_at'
        START_TIME = 'start_time'
        END_TIME = 'end_time'
        NOTES = 'notes'
        META = 'meta'

        DATAPOINTS = 'datapoints'
        DEVICES = 'devices'
        PROJECTS = 'projects'
        TAGS = 'tags'
        USERS = 'users'


    id: Optional[SessionID_t] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    active: bool = Field(default=False)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_dt, nullable=False)
    updated_at: datetime = Field(default_factory=get_utc_dt, nullable=False)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    meta: Optional[dict] = Field(sa_column=Column(JSONB), default=None)

    datapoints: list['DataPoint'] = Relationship(
        back_populates="sessions",
        link_model=SessionDataPointLink
    )

    devices: list['Device'] = Relationship(
        back_populates="sessions",
        link_model=SessionDeviceLink
    )

    projects: list['Project'] = Relationship(
        back_populates="sessions",
        link_model=SessionProjectLink
    )

    tags: list['Tag'] = Relationship(
        back_populates="sessions",
        link_model=SessionTagLink
    )

    users: list['User'] = Relationship(
        back_populates="sessions",
        link_model=SessionUserLink
    )

@event.listens_for(Session, "before_update")
def update_timestamp(_mapper, _connection, target):
    target.updated_at = get_utc_dt()

class Sessions:
    def __init__(self, sessions: list[Session] = None):
        if sessions is None:
            self._sessions = list()
        else:
            self._sessions = sessions
        self.sort()

    def append(self, session: Session):
        self._sessions.append(session)

    def sort(self, reverse: bool = False):
        """Sort tags in place by name."""
        self._sessions.sort(key=lambda tag: tag.name.lower(), reverse=reverse)

    def __getitem__(self, index):
        return self._sessions[index]

    def __len__(self):
        return len(self._sessions)

    def __iter__(self) -> Iterator[Session]:
        return iter(self._sessions)

    def __str__(self):
        table = PrettyTable(title='Sessions')
        # Use Tag.Key enum values for headers
        table.field_names = [str(x) for x in Session.Key]

        # Wrap text for description and sessions
        table.align[User.Key.NAME] = 'l'
        table.align[User.Key.EMAIL] = 'l'

        for user in self._sessions:
            # Prepare session list string
            session_names = [f'{s.name}' for s in user.sessions]  # Could be id or start_ts
            session_str = ', '.join(session_names)
            wrapped_sessions = textwrap.fill(session_str, width=TABLE_COLUMN_WIDTH)

            table.add_row([
                user.id,
                user.name,
                user.email,
                wrapped_sessions
            ])

        return str(table)

class SessionEngine(BaseTableEngine):
    def get(self, session_id: SessionID_t) -> Session:
        ...

    def list(self) -> Sessions:
        ...

    def remove(self, sess: Session):
        ...

    def upsert(self, model: Session, update_fields: Optional[dict] = None) -> Session:
        return super().upsert(
            model,
            # {User.Key.NAME: model.name, User.Key.EMAIL: model.email}
        )