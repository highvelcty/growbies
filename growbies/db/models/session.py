from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from .common import BaseTableEngine
from growbies.utils.types import SessionID_t

if TYPE_CHECKING:
    from .datapoint import DataPoint
    from .device import Device
    from .tag import Tag


class SessionDataPointLink(SQLModel, table=True):
    session_id: int = Field(foreign_key="session.id", primary_key=True)
    datapoint_id: int = Field(foreign_key="datapoint.id", primary_key=True)

class SessionDeviceLink(SQLModel, table=True):
    session_id: int = Field(foreign_key="session.id", primary_key=True)
    device_id: int = Field(foreign_key="device.id", primary_key=True)

class SessionTagLink(SQLModel, table=True):
    session_id: int = Field(foreign_key="session.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)

class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None

    active_devices: List['Device'] = Relationship(
        back_populates="active_sessions",
        link_model=SessionDeviceLink
    )

    datapoints: List['DataPoint'] = Relationship(
        back_populates="sessions",
        link_model=SessionDataPointLink
    )

    tags: List['Tag'] = Relationship(
        back_populates="sessions",
        link_model=SessionTagLink
    )

class SessionEngine(BaseTableEngine):
    def add(self, sess: Session):
        pass

    def remove(self, sess: Session):
        pass

    def get(self, session_id: SessionID_t) -> list[Session]:
        pass
