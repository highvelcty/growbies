from sqlmodel import SQLModel, Field

class SessionDataPointLink(SQLModel, table=True):
    session_id: int = Field(foreign_key="session.id", primary_key=True)
    datapoint_id: int = Field(foreign_key="datapoint.id", primary_key=True)

class SessionDeviceLink(SQLModel, table=True):
    session_id: int = Field(foreign_key="session.id", primary_key=True)
    device_id: int = Field(foreign_key="device.id", primary_key=True)

class SessionTagLink(SQLModel, table=True):
    session_id: int = Field(foreign_key="session.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)

class SessionUserLink(SQLModel, table=True):
    session_id: int = Field(foreign_key="session.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)