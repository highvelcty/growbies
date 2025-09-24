from abc import ABC
from typing import TYPE_CHECKING

from sqlmodel import SQLModel, select

if TYPE_CHECKING:
    from growbies.db.engine import DBEngine


class BaseTableEngine(ABC):
    def __init__(self, engine: 'DBEngine'):
        self._engine = engine

    def upsert(self, model: SQLModel):
        with self._engine.new_session() as session:
            stmt = (
                select(type(model))
                .where(type(model).name == model.name)
                .with_for_update()
            )
            # noinspection PyTypeChecker
            existing_account = session.exec(stmt).first()

            if existing_account:
                return existing_account
            else:
                session.add(model)
                session.commit()
                session.refresh(model)
            return model
