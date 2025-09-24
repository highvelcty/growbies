from abc import ABC
from typing import Generic, Optional, TYPE_CHECKING, TypeVar

from sqlmodel import SQLModel, select

if TYPE_CHECKING:
    from growbies.db.engine import DBEngine


TSQLModel = TypeVar('TSQLModel', bound='SQLModel')

class BaseTableEngine(Generic[TSQLModel], ABC):
    def __init__(self, engine: 'DBEngine'):
        self._engine = engine

    def upsert(self, model: TSQLModel, update_fields: Optional[dict] = None) -> TSQLModel:
        with self._engine.new_session() as session:
            stmt = (
                select(type(model))
                .where(type(model).name == model.name)
                .with_for_update()
            )
            existing = session.exec(stmt).first()

            if existing:
                if update_fields:
                    for key, value in update_fields.items():
                        setattr(existing, key, value)
                session.add(existing)  # ensures SQLModel tracks it
                session.commit()
                session.refresh(existing)
                return existing
            else:
                session.add(model)
                session.commit()
                session.refresh(model)
                return model
