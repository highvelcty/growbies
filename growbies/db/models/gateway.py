from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Column, Field, Relationship

from .common import BaseTable, BaseNamedTableEngine, SortedTable

if TYPE_CHECKING:
    from .account import Account
    from .device import Device
from growbies.utils.types import FuzzyID

class Gateway(BaseTable, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'
        ACCOUNTS = 'accounts'
        DEVICES = 'devices'

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    account: UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey(
                f'account.id',
                ondelete="CASCADE"
            ),
            nullable=False
        )
    )

    accounts: 'Account' = Relationship(back_populates='gateways')
    devices: list['Device'] = Relationship(back_populates='gateways', cascade_delete=True)

class Gateways(SortedTable[Gateway]):
    pass

class GatewayEngine(BaseNamedTableEngine):
    model_class = Gateway

    def get(self, fuzzy_id: FuzzyID) -> Gateway:
        return self._get_one(fuzzy_id, self.model_class.devices)

    def get_multi(self, fuzzy_id: FuzzyID) -> Gateways:
        return Gateways(self._get_multi(fuzzy_id, self.model_class.devices))
