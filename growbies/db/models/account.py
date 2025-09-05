from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, String

if TYPE_CHECKING:
    from .gateway import Gateway

from .common import BaseTableEngine


class Account(SQLModel, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))

    gateways: list['Gateway'] = Relationship(back_populates='account_relation', cascade_delete=True)

class AccountEngine(BaseTableEngine): pass
