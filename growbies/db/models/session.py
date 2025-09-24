from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import Column, SQLModel, Field, Relationship
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB

from .common import BaseTableEngine
from .links import SessionDataPointLink, SessionDeviceLink, SessionUserLink, SessionTagLink
from growbies.utils.timestamp import get_utc_dt
from growbies.utils.types import SessionID_t

if TYPE_CHECKING:
    from .datapoint import DataPoint
    from .device import Device
    from .tag import Tag
    from .user import User

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    active: bool = Field(default=False)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_dt, nullable=False)
    updated_at: datetime = Field(default_factory=get_utc_dt, nullable=False)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    meta: Optional[dict] = Field(sa_column=Column(JSONB), default=None)

    # Edric, uncommenting any of the following relationships causes a circular import problem
    participants: list['User'] = Relationship(
        back_populates="sessions",
        link_model=SessionUserLink
    )

    devices: list['Device'] = Relationship(
        back_populates="sessions",
        link_model=SessionDeviceLink
    )

    datapoints: list['DataPoint'] = Relationship(
        back_populates="sessions",
        link_model=SessionDataPointLink
    )

    tags: list['Tag'] = Relationship(
        back_populates="sessions",
        link_model=SessionTagLink
    )

@event.listens_for(Session, "before_update")
def update_timestamp(mapper, connection, target):
    target.updated_at = get_utc_dt()

class SessionEngine(BaseTableEngine):
    def add(self, sess: Session):
        pass

    def remove(self, sess: Session):
        pass

    def get(self, session_id: SessionID_t) -> Session:
        pass
