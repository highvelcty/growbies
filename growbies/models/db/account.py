from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, String

from .base import KeyStr
if TYPE_CHECKING:
    from .gateway import Gateway

class Account(SQLModel, table=True):
    class Key:
        ID: KeyStr = 'id'
        NAME: KeyStr = 'name'

    id: int = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))

    gateways: list['Gateway'] = Relationship(back_populates='account_relation', cascade_delete=True)