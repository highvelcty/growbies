from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel, select
from sqlalchemy import Column, String

if TYPE_CHECKING:
    from .gateway import Gateway
    from growbies.db.engine import DBEngine


class Account(SQLModel, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))

    gateways: list['Gateway'] = Relationship(back_populates='account_relation', cascade_delete=True)

class AccountEngine:
    def __init__(self, engine: 'DBEngine'):
        self._engine = engine

    def upsert(self, account: Account):
        with self._engine.new_session() as session:
            stmt = (
                select(Account)
                .where(Account.name == account.name)
                .with_for_update()
            )
            # noinspection PyTypeChecker
            existing_account = session.exec(stmt).first()

            if existing_account:
                return existing_account
            else:
                session.add(account)
                session.commit()
                session.refresh(account)
            return account
