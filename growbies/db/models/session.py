from datetime import datetime
from enum import StrEnum
from typing import Iterator, List, Optional, TYPE_CHECKING
import textwrap
import uuid
import logging

logger = logging.getLogger(__name__)

from prettytable import PrettyTable
from sqlalchemy import cast, event, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import String
from sqlmodel import Column, select, SQLModel, Field, Relationship

from .common import BaseTableEngine
from .links import (SessionDataPointLink, SessionDeviceLink, SessionProjectLink, SessionTagLink,
                    SessionUserLink)
from growbies.cli.session import Action, Entity
from growbies.service.common import ServiceCmdError
from growbies.constants import TABLE_COLUMN_WIDTH
from growbies.utils.timestamp import get_utc_dt
from growbies.utils.types import DeviceID_t, ProjectID_t, SessionID_t, TagID_t, UserID_t

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
        table.field_names = (Session.Key.ID, Session.Key.NAME, Session.Key.DESCRIPTION)

        for field in table.field_names:
            table.align[field] = 'l'

        for sess in self._sessions:
            table.add_row([
                sess.id,
                sess.name,
                sess.description,
            ])

        return str(table)

class SessionEngine(BaseTableEngine):
    def add(self, name: str, entity: Entity, *names: str):
        ...

    def get(self, name_or_id: str) -> Session:
        return self._get_by_name_or_id(name_or_id)[0]

    def rm(self, name: str, action: Action, entity: Entity, *names: str):
        ...

    def ls(self) -> Sessions:
        with self._engine.new_session() as sess:
            sessions = sess.exec(select(Session)).all()
        return Sessions(sessions)

    def _get_by_name_or_id(self, name_or_id: str) -> list[Session]:
        with self._engine.new_session() as sess:  # SQLModel session
            stmt = select(Session).where(
                or_(
                    Session.name == name_or_id,
                    cast(Session.id, String).like(f"{name_or_id}%")
                )
            )
            results = sess.exec(stmt).all()

        if not results:
            raise ServiceCmdError('No results')
        elif len(results) > 1:
            raise ServiceCmdError(f'Multiple hits for "{name_or_id}".')
        return results

    def remove(self, name_or_id: str):
        """Remove a session by name or partial/full UUID."""
        # Look up session(s) by name or ID prefix
        sessions = self._get_by_name_or_id(name_or_id)

        # At this point, _get_by_name_or_id guarantees exactly one result
        session_to_remove = sessions[0]

        with self._engine.new_session() as sess:
            sess.delete(session_to_remove)
            sess.commit()

    def upsert(self, model: Session, update_fields: Optional[dict] = None) -> Session:
        return super().upsert(
            model,
            {Session.Key.NAME: model.name, Session.Key.ACTIVE: model.active,
             Session.Key.DESCRIPTION: model.description, Session.Key.NOTES: model.notes,
             Session.Key.META: model.meta, Session.Key.DEVICES: model.devices,
             Session.Key.PROJECTS: model.projects, Session.Key.TAGS: model.tags,
             Session.Key.USERS: model.users}
        )
