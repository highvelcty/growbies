from enum import IntEnum

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, Integer, ForeignKey, String

from .base import KeyStr
from .device import Device


class EndpointType(IntEnum):
    MASS        = 0
    TEMPERATURE = 1

class Endpoint(SQLModel, table=True):
    class Key:
        ID: KeyStr = 'id'
        NAME: KeyStr = 'name'
        DEVICE: KeyStr = 'device'

    id: int = Field(default=None, primary_key=True)
    device: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Device.__tablename__}.id',
                ondelete="CASCADE"
            ),
            nullable=False
        )
    )
    index: int
    type: EndpointType

    device_relation: Device = Relationship(back_populates='endpoints')
