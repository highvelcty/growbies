from datetime import datetime
from enum import StrEnum
from typing import Callable, Optional, TYPE_CHECKING
import uuid
import logging

logger = logging.getLogger(__name__)

from prettytable import PrettyTable
from sqlalchemy import exists, event, func, inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, select, Field, Relationship

from .common import BaseTable, BaseNamedTableEngine, BuiltinTagName, SortedTable, TSQLModel
from .link import (SessionDataPointLink, SessionDeviceLink, SessionProjectLink, SessionTagLink,
                   SessionUserLink)
from growbies.cli.session import Entity
from growbies.utils.report import list_str_wrap, short_uuid, wrap_for_column
from growbies.utils.timestamp import get_utc_dt
from growbies.utils.types import DeviceID, SessionID

from .datapoint import DataPoint
if TYPE_CHECKING:
    from .device import Device
    from .project import Project
    from .tag import Tag
    from .user import User

class Session(BaseTable, table=True):
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

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
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

    @property
    def datapoint_count(self) -> int:
        return getattr(self, '_datapoint_count', 0)

    @datapoint_count.setter
    def datapoint_count(self, value: int):
        # Initialized at runtime to avoid compile time pydantic/sqlmodel/sqlalchemy interception.
        # noinspection PyAttributeOutsideInit
        self._datapoint_count = value

    def __str__(self):
        def format_multiline(text, indent=4):
            if not text:
                return ''
            lines_ = text.split('\n')
            if len(lines_) == 1:
                return text
            return '\n' + '\n'.join(' ' * indent + line for line in lines_)

        devices_str = list_str_wrap(
            [f'{dev.name} ({short_uuid(dev.id)})' for dev in self.devices],
            indent=len(self.Key.DEVICES) + 3
        )
        projects_str = list_str_wrap(
            [f'{proj.name} ({short_uuid(proj.id)})' for proj in self.projects],
            indent=len(self.Key.PROJECTS) + 3
        )
        tags_str = list_str_wrap(
            [f'{tag.name} ({short_uuid(tag.id)})' for tag in self.tags],
            indent=len(self.Key.TAGS) + 3
        )
        users_str = list_str_wrap(
            [f'{user.name} ({short_uuid(user.id)})' for user in self.users],
            indent=len(self.Key.USERS) + 3
        )

        lines = [
            f'{self.Key.ID}: {self.id}',
            f'{self.Key.NAME}: {self.name}',
            f'{self.Key.ACTIVE}: {self.active}',
            f'{self.Key.DESCRIPTION}: {format_multiline(self.description)}',
            f'{self.Key.CREATED_AT}: {self.created_at}',
            f'{self.Key.UPDATED_AT}: {self.updated_at}',
            f'{self.Key.START_TIME}: {self.start_time or ""}',
            f'{self.Key.END_TIME}: {self.end_time or ""}',
            f'{self.Key.NOTES}: {format_multiline(self.notes)}',
            f'{self.Key.META}: {self.meta or ""}',
            f'datapoint count: {self.datapoint_count}',
            f'{self.Key.DEVICES}: {devices_str}',
            f'{self.Key.PROJECTS}: {projects_str}',
            f'{self.Key.TAGS}: {tags_str}',
            f'{self.Key.USERS}: {users_str}'
        ]
        return '\n'.join(lines)

@event.listens_for(Session, "before_update")
def update_timestamp(_mapper, _connection, target: Session):
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

class Sessions(SortedTable[Session]):
    def __init__(self, *args,
                 show_active: bool = True,
                 show_id: bool = True,
                 show_device_ids: bool = False,
                 show_device_names: bool = False,
                 show_name: bool = True,
                 show_description = True,
                 show_notes = True,
                 **kw):
        super().__init__(*args, **kw)
        self._show_active = show_active
        self._show_id = show_id
        self._show_device_ids = show_device_ids
        self._show_device_names = show_device_names
        self._show_name = show_name
        self._show_description = show_description
        self._show_notes = show_notes

    @property
    def show_active(self) -> bool:
        return self._show_active

    @show_active.setter
    def show_active(self, value: bool):
        self._show_active = value

    @property
    def show_id(self) -> bool:
        return self._show_id

    @show_id.setter
    def show_id(self, value: bool):
        self._show_id = value

    @property
    def show_device_ids(self) -> bool:
        return self._show_device_ids

    @show_device_ids.setter
    def show_device_ids(self, value: bool):
        self._show_device_ids = value

    @property
    def show_device_names(self) -> bool:
        return self._show_device_names

    @show_device_names.setter
    def show_device_names(self, value: bool):
        self._show_device_names = value

    @property
    def show_name(self) -> bool:
        return self._show_name

    @show_name.setter
    def show_name(self, value: bool):
        self._show_name = value

    @property
    def show_description(self) -> bool:
        return self._show_description

    @show_description.setter
    def show_description(self, value: bool):
        self._show_description = value

    @property
    def show_notes(self) -> bool:
        return self._show_notes

    @show_notes.setter
    def show_notes(self, value: bool):
        self._show_notes = value



    def __str__(self):
        table = PrettyTable(title=self.table_name())
        table.preserve_internal_whitespace = True

        field_names = list()
        if self._show_id:
            field_names.append(Session.Key.ID)
        if self._show_name:
            field_names.append(Session.Key.NAME)
        if self._show_device_ids:
            field_names.append('Device IDs')
        if self._show_device_names:
            field_names.append('Device Names')
        if self._show_active:
            field_names.append(Session.Key.ACTIVE)
        if self._show_description:
            field_names.append(Session.Key.DESCRIPTION)
        if self._show_notes:
            field_names.append(Session.Key.NOTES)

        table.field_names = field_names

        for field in table.field_names:
            table.align[field] = 'l'

        for sess in self._rows:
            row = list()
            if self._show_id:
                row.append(short_uuid(sess.id))
            if self._show_name:
                row.append(sess.name)
            if self._show_device_ids:
                row.append(
                    wrap_for_column(', '.join(short_uuid(dev.id) for dev in sess.devices),
                                    max_column_width=self.max_column_width)
                )
            if self._show_device_names:
                row.append(
                    wrap_for_column(
                        ', '.join(
                            dev.name if dev.name != str(dev.id) else short_uuid(dev.name)
                            for dev in sess.devices
                        ),
                        max_column_width=self.max_column_width
                    )
                )
            if self._show_active:
                row.append(sess.active)
            if self._show_description:
                row.append(wrap_for_column(sess.description,
                                           max_column_width=self.max_column_width))
            if self._show_notes:
                row.append(wrap_for_column(sess.notes,
                                           max_column_width=self.max_column_width))

            table.add_row(row)

        return str(table)

class SessionEngine(BaseNamedTableEngine):
    model_class = Session

    def add_entity(self, sess_name_or_id: str, entity: Entity, *entity_names_or_ids: str):
        sess = self.get(sess_name_or_id)

        if entity == Entity.DEVICE:
            link_engine = self._engine.link.session_device
            get_entity = self._engine.device.get
        elif entity == Entity.PROJECT:
            link_engine = self._engine.link.session_project
            get_entity = self._engine.project.get
        elif entity == Entity.TAG:
            link_engine = self._engine.link.session_tag
            get_entity = self._engine.tag.get
        elif entity == Entity.USER:
            link_engine = self._engine.link.session_user
            get_entity = self._engine.user.get
        else:
            raise ValueError(f"Unsupported entity type: {entity}")

        for entity_name_or_id in entity_names_or_ids:
            i_entity = get_entity(entity_name_or_id)
            link_engine.add(sess.id, i_entity.id)

    def get(self, fuzzy_id: str) -> Session:
        sess = self._get_one(fuzzy_id, Session.devices, Session.projects, Session.tags,
                             Session.users)
        self._populate_datapoint_count(sess)
        return sess

    def get_active_by_device_id(self, device_id: DeviceID) -> Sessions:
        with self._engine.new_session() as db_sess:
            # Python syntax, building SQL expressions
            # noinspection PyTypeChecker
            stmt = (
                select(self.model_class)
                .join(SessionDeviceLink)
                .where(
                    SessionDeviceLink.right_id == device_id,
                    self.model_class.active == True
                )
            )
            results = db_sess.exec(stmt).all()
            return Sessions(results)

    def get_calibration_restorable_devices(self, session_id: SessionID) -> list[DeviceID]:
        """
        A calibration restorable device is any device in this session that does not have an
        additional active calibration session linked to it. A calibration session differs from aa
        regular session by a calibration tag.
        """
        # Runtime import to avoid circular dependencies.
        from .tag import Tag
        with self._engine.new_session() as db:
            # noinspection PyTypeChecker,PyUnresolvedReferences
            other_active_cal = (
                select(SessionDeviceLink.right_id)
                .join(Session, Session.id == SessionDeviceLink.left_id)
                .join(SessionTagLink, SessionTagLink.left_id == Session.id)
                .join(Tag, Tag.id == SessionTagLink.right_id)
                .where(
                    Session.id != session_id,
                    Session.active.is_(True),
                    Tag.name == BuiltinTagName.CALIBRATION
                )
            )

            stmt = (
                select(SessionDeviceLink.right_id)
                .where(SessionDeviceLink.left_id == session_id)
                .where(~exists(other_active_cal))
            )

            return db.exec(stmt).all()

    def get_datapoints(self, session_id: SessionID) -> list['DataPoint']:
        with self._engine.new_session() as db:
            # noinspection PyTypeChecker
            stmt = (
                select(DataPoint)
                .join(SessionDataPointLink, SessionDataPointLink.right_id == DataPoint.id)
                .where(SessionDataPointLink.left_id == session_id)
                .order_by(DataPoint.timestamp)
            )

            return db.exec(stmt).all()

    def list(self) -> Sessions:
        """Return all sessions with links eagerly loaded, using base class accessors."""
        return Sessions(self._get_all(Session.devices, Session.projects, Session.tags,
                                      Session.users))

    def prefix_list(self, prefix: str) -> Sessions:
        """Return sessions whose name starts with the given prefix, as DTOs."""
        with self._engine.new_session() as db:
            # noinspection PyUnresolvedReferences
            stmt = select(self.model_class).where(self.model_class.name.like(f"{prefix}%"))
            orm_sessions = db.exec(stmt).all()
            return Sessions(orm_sessions)

    def remove_entity(self, sess_name_or_id: str, entity: Entity, *entity_names_or_ids: str):
        sess = self.get(sess_name_or_id)

        if entity == Entity.DEVICE:
            link_engine = self._engine.link.session_device
            get_entity = self._engine.device.get
        elif entity == Entity.PROJECT:
            link_engine = self._engine.link.session_project
            get_entity = self._engine.project.get
        elif entity == Entity.TAG:
            link_engine = self._engine.link.session_tag
            get_entity = self._engine.tag.get
        elif entity == Entity.USER:
            link_engine = self._engine.link.session_user
            get_entity = self._engine.user.get
        else:
            raise ValueError(f"Unsupported entity type: {entity}")

        for entity_name_or_id in entity_names_or_ids:
            i_entity = get_entity(entity_name_or_id)
            link_engine.remove(sess.id, i_entity.id)

    def upsert(self, model: Session, fields: Optional[dict] = None) -> Session:
        _fields = {
            Session.Key.NAME: model.name,
            Session.Key.ACTIVE: model.active,
            Session.Key.DESCRIPTION: model.description,
            Session.Key.NOTES: model.notes,
            Session.Key.META: model.meta,
        }
        if fields:
            _fields.update(fields)

        return super().upsert(model, _fields)

    def _populate_datapoint_count(self, session: Session) -> None:
        with self._engine.new_session() as db:
            count_stmt = select(func.count()).where(
                SessionDataPointLink.left_id == session.id
            )
            session.datapoint_count = db.exec(count_stmt).first()