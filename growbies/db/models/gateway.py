from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, Integer, ForeignKey, String

from .common import BaseTableEngine
from .account import Account

if TYPE_CHECKING:
    from .device import Device

class Gateway(SQLModel, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'
        ACCOUNT = 'account'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    account: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Account.__tablename__}.id',
                ondelete="CASCADE"
            ),
            nullable=False
        )
    )

    account_relation: Account = Relationship(back_populates='gateways')
    devices: list['Device'] = Relationship(back_populates='gateway_relation', cascade_delete=True)

class GatewayEngine(BaseTableEngine): pass
