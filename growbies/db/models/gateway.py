from typing import Iterator, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, Relationship, SQLModel

from .common import BaseTable, BaseNamedTableEngine, SortedTable
from .account import Account
from growbies.utils.types import AccountID_t, GatewayID_t

if TYPE_CHECKING:
    from .device import Device

class Gateway(BaseTable, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'
        ACCOUNT = 'account'

    id: Optional[GatewayID_t] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    account: AccountID_t = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey(
                f'{Account.__tablename__}.id',
                ondelete="CASCADE"
            ),
            nullable=False
        )
    )

    accounts: Account = Relationship(back_populates='gateways')
    devices: list['Device'] = Relationship(back_populates='gateways', cascade_delete=True)

class Gateways(SortedTable[Gateway]):
    pass

class GatewayEngine(BaseNamedTableEngine):
    model_class = Gateway

    def get(self, fuzzy_id: str | UUID) -> Gateway:
        return self._get_one(fuzzy_id, self.model_class.devices)

    def get_multi(self, fuzzy_id: str | UUID) -> Gateways:
        return Gateways(self._get_multi(fuzzy_id, self.model_class.devices))
