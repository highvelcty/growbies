from typing import TYPE_CHECKING
import uuid

from sqlmodel import Column, Field
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import ForeignKey

from .common import BaseLink
from growbies.db.models.common import BaseLinkEngine
if TYPE_CHECKING:
    from growbies.db.engine import DBEngine

__all__ = [
    # link tables
    'SessionDataPointLink', 'SessionDeviceLink', 'SessionProjectLink', 'SessionTagLink',
    'SessionUserLink',
    # engines
    'SessionDataPointLinkEngine', 'SessionDeviceLinkEngine',
    'SessionProjectLinkEngine', 'SessionUserLinkEngine', 'LinkEngine']

class SessionDataPointLink(BaseLink, table=True):
    left_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('session.id', ondelete='CASCADE'),
                         primary_key=True)
    )
    right_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('datapoint.id', ondelete='CASCADE'),
                         primary_key=True)
    )

class SessionDeviceLink(BaseLink, table=True):
    left_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('session.id', ondelete='CASCADE'),
                         primary_key=True)
    )
    right_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('device.id', ondelete='CASCADE'),
                         primary_key=True)
    )

class SessionProjectLink(BaseLink, table=True):
    left_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('session.id', ondelete='CASCADE'),
                         primary_key=True)
    )
    right_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('project.id', ondelete='CASCADE'),
                         primary_key=True)
    )

class SessionTagLink(BaseLink, table=True):
    left_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('session.id', ondelete='CASCADE'),
                         primary_key=True)
    )
    right_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('tag.id', ondelete='CASCADE'),
                         primary_key=True)
    )

class SessionUserLink(BaseLink, table=True):
    left_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('session.id', ondelete='CASCADE'),
                         primary_key=True)
    )
    right_id: uuid.UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True),
                         ForeignKey('user.id', ondelete='CASCADE'),
                         primary_key=True)
    )

class SessionDataPointLinkEngine(BaseLinkEngine):
    model_class = SessionDataPointLink

class SessionDeviceLinkEngine(BaseLinkEngine):
    model_class = SessionDeviceLink

class SessionProjectLinkEngine(BaseLinkEngine):
    model_class = SessionProjectLink

class SessionTagLinkEngine(BaseLinkEngine):
    model_class = SessionTagLink

class SessionUserLinkEngine(BaseLinkEngine):
    model_class = SessionUserLink

class LinkEngine:
    def __init__(self, engine: 'DBEngine'):
        self.session_datapoint = SessionDataPointLinkEngine(engine)
        self.session_device = SessionDeviceLinkEngine(engine)
        self.session_project = SessionProjectLinkEngine(engine)
        self.session_tag = SessionTagLinkEngine(engine)
        self.session_user = SessionUserLinkEngine(engine)
