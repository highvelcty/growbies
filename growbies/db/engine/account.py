from typing import TYPE_CHECKING
from sqlmodel import select

if TYPE_CHECKING:
    from growbies.db.engine import DBEngine
from growbies.db.models import Account

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
