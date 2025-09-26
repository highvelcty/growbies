from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import SQLModel, Field

from growbies.utils.types import SessionID_t, DataPointID_t, DeviceID_t, TagID_t, UserID_t

class SessionDataPointLink(SQLModel, table=True):
    session_id: SessionID_t = Field(
        sa_column=Column(UUID(as_uuid=True),
                         ForeignKey("session.id", ondelete="CASCADE"),
                         primary_key=True)
    )
    datapoint_id: DataPointID_t = Field(
        sa_column=Column(UUID(as_uuid=True),
                         ForeignKey("datapoint.id", ondelete="CASCADE"),
                         primary_key=True)
    )


class SessionDeviceLink(SQLModel, table=True):
    session_id: SessionID_t = Field(
        sa_column=Column(UUID(as_uuid=True),
                         ForeignKey("session.id", ondelete="CASCADE"),
                         primary_key=True)
    )
    device_id: DeviceID_t = Field(
        sa_column=Column(UUID(as_uuid=True),
                         ForeignKey("device.id", ondelete="CASCADE"),
                         primary_key=True)
    )

class SessionTagLink(SQLModel, table=True):
    session_id: SessionID_t = Field(
        sa_column=Column(UUID(as_uuid=True),
                         ForeignKey("session.id", ondelete="CASCADE"),
                         primary_key=True)
    )
    tag_id: TagID_t = Field(
        sa_column=Column(UUID(as_uuid=True),
                         ForeignKey("tag.id", ondelete="CASCADE"),
                         primary_key=True)
    )

class SessionUserLink(SQLModel, table=True):
    session_id: SessionID_t = Field(
        sa_column=Column(UUID(as_uuid=True),
                         ForeignKey("session.id", ondelete="CASCADE"),
                         primary_key=True)
    )
    user_id: UserID_t = Field(
        sa_column=Column(UUID(as_uuid=True),
                         ForeignKey("user.id", ondelete="CASCADE"),
                         primary_key=True)
    )
