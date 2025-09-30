from datetime import datetime
from enum import StrEnum
from typing import Iterator, List, Optional, TYPE_CHECKING
import textwrap
import uuid
import logging

logger = logging.getLogger(__name__)

from prettytable import PrettyTable
from sqlalchemy import cast, event, inspect,  or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import selectinload
from sqlalchemy.types import String
from sqlmodel import Column, select, SQLModel, Field, Relationship

from .common import BaseTableEngine
from .links import (SessionDataPointLink, SessionDeviceLink, SessionProjectLink, SessionTagLink,
                    SessionUserLink)
from growbies.cli.session import Action, Entity
from growbies.service.common import ServiceCmdError
from growbies.constants import TABLE_COLUMN_WIDTH
from growbies.utils.report import decode_escapes, list_str_wrap, short_uuid, wrap_for_column
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

    def __str__(self):
        def format_multiline(text, indent=4):
            if not text:
                return ''
            lines_ = text.split('\n')
            if len(lines_) == 1:
                return text
            return '\n' + '\n'.join(' ' * indent + line for line in lines_)

        lines = [
            f'id: {self.id}',
            f'name: {self.name}',
            f'active: {self.active}',
            f'description:{format_multiline(self.description)}',
            f'created_at: {self.created_at}',
            f'updated_at: {self.updated_at}',
            f'start_time: {self.start_time or ""}',
            f'end_time: {self.end_time or ""}',
            f'notes: {format_multiline(self.notes)}',
            f'meta: {self.meta or ""}',
            f'devices: {list_str_wrap(self.devices)}',
            f'projects: {list_str_wrap(self.projects)}',
            f'tags: {list_str_wrap(self.tags)}',
            f'users: {list_str_wrap(self.users)}'
        ]
        return '\n'.join(lines)

@event.listens_for(Session, "before_update")
def update_timestamp(mapper, connection, target: Session):
    # always update the "last modified" timestamp
    target.updated_at = get_utc_dt()

    state = inspect(target)

    if Session.Key.ACTIVE in state.attrs:
        hist = state.attrs.active.history

        # Detect actual changes to `active`
        if hist.has_changes() and hist.deleted and hist.added:
            old_val, new_val = hist.deleted[0], hist.added[0]

            # Transition: False -> True
            if old_val is False and new_val is True:
                if target.start_time is None:
                    target.start_time = get_utc_dt()
                # clear any prior end_time on re-activation
                target.end_time = None

            # Transition: True -> False
            if old_val is True and new_val is False:
                target.end_time = get_utc_dt()

class Sessions:
    def __init__(self, rows: list[Session] = None):
        if rows is None:
            self._rows = list()
        else:
            self._rows = rows
        self.sort()

    @classmethod
    def table_name(cls):
        return cls.__qualname__

    def append(self, session: Session):
        self._rows.append(session)

    def sort(self, reverse: bool = False):
        """Sort tags in place by name."""
        self._rows.sort(key=lambda tag: tag.name.lower(), reverse=reverse)

    def __getitem__(self, index):
        return self._rows[index]

    def __len__(self):
        return len(self._rows)

    def __iter__(self) -> Iterator[Session]:
        return iter(self._rows)

    def __str__(self):
        table = PrettyTable(title=self.table_name())
        table.preserve_internal_whitespace = True
        table.field_names = (Session.Key.ID, Session.Key.NAME, Session.Key.ACTIVE,
                             Session.Key.DESCRIPTION, Session.Key.NOTES)

        for field in table.field_names:
            table.align[field] = 'l'

        for sess in self._rows:
            table.add_row([
                short_uuid(sess.id),
                sess.name,
                sess.active,
                wrap_for_column(sess.description),
                wrap_for_column(sess.notes)
            ])

        return str(table)

class SessionEngine(BaseTableEngine):
    def add(self, name: str, entity: Entity, *names: str):
        ...

    def get(self, name_or_id: str) -> Session:
        return self._get_one_by_name_or_id(name_or_id)

    def rm(self, name: str, action: Action, entity: Entity, *names: str):
        ...

    def ls(self) -> Sessions:
        with self._engine.new_session() as sess:
            sessions = sess.exec(select(Session)).all()
        return Sessions(sessions)

    def _get_multi_by_name_or_id(self, name_or_id: str) -> list[Session]:
        """
        Case-insensitive, match anywhere in name or ID.
        """
        with self._engine.new_session() as sess:  # SQLModel session
            stmt = select(Session).where(
                or_(
                    cast(Session.name, String).ilike(f"%{name_or_id}%"),  # Partial name match
                    cast(Session.id, String).ilike(f"{name_or_id}%")  # Partial ID match (prefix)
                )
            ).options(
                selectinload(Session.devices),
                selectinload(Session.projects),
                selectinload(Session.tags),
                selectinload(Session.users)
            )
            return sess.exec(stmt).all()

    def _get_one_by_name_or_id(self, name_or_id: str) -> Session:
        results = self._get_multi_by_name_or_id(name_or_id)
        if not results:
            raise ServiceCmdError(f'No results for "{name_or_id}".')
        elif len(results) > 1:
            raise ServiceCmdError(f'Multiple results for "{name_or_id}".')
        return results[0]

    def remove(self, name_or_id: str):
        """Remove a session by name or partial/full UUID."""
        sess_to_remove = self._get_one_by_name_or_id(name_or_id)
        with self._engine.new_session() as sess:
            sess.delete(sess_to_remove)
            sess.commit()

    def upsert(self, model: Session, update_fields: Optional[dict] = None) -> Session:
        return super().upsert(
            model,
            {Session.Key.NAME: model.name, Session.Key.ACTIVE: model.active,
             Session.Key.DESCRIPTION: decode_escapes(model.description),
             Session.Key.NOTES: decode_escapes(model.notes),
             Session.Key.META: model.meta}
        )
