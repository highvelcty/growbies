from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Column, String
from sqlmodel import Field, Relationship, SQLModel


from .common import BaseTable, BaseNamedTableEngine
if TYPE_CHECKING:
    from . import Gateway
from growbies.utils.types import AccountID_t

class Account(BaseTable, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'

    id: Optional[AccountID_t] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))

    gateways: list['Gateway'] = Relationship(back_populates='account_relation', cascade_delete=True)

class AccountEngine(BaseNamedTableEngine):
    model_class = Account
