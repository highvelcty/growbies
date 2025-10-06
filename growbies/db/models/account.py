from uuid import UUID
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship

from .common import BaseTable, BaseNamedTableEngine, SortedTable
if TYPE_CHECKING:
    from . import Gateway
from growbies.utils.types import AccountID_t

class Account(BaseTable, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'

    id: Optional[AccountID_t] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))

    gateways: list['Gateway'] = Relationship(back_populates='accounts', cascade_delete=True)

class Accounts(SortedTable[Account]):
    pass

class AccountEngine(BaseNamedTableEngine):
    model_class = Account

    def get(self, fuzzy_id: str | UUID) -> Account:
        return self._get_one(fuzzy_id, self.model_class.devices)

    def get_multi(self, fuzzy_id: str | UUID) -> Accounts:
        return Accounts(self._get_multi(fuzzy_id, self.model_class.gateways))