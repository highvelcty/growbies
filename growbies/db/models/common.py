from abc import ABC
from typing import Any, Generic, Iterator, Optional, TYPE_CHECKING, Type, TypeVar
from uuid import UUID

from sqlalchemy import cast, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.types import String
from sqlmodel import SQLModel, select

if TYPE_CHECKING:
    from growbies.db.engine import DBEngine
from growbies.service.common import ServiceCmdError
from growbies.utils.report import short_uuid


TSQLModel = TypeVar('TSQLModel', bound='BaseTable')

class BaseTable(SQLModel):
    id: Any

    @property
    def short_uuid(self) -> str:
        return short_uuid(self.id)


class BaseTableEngine(Generic[TSQLModel], ABC):
    model_class: Type[TSQLModel]

    def __init__(self, engine: 'DBEngine'):
        self._engine = engine

class BaseNamedTableEngine(BaseTableEngine):

    def _make_get_stmt(self, fuzzy_id: str | UUID):
        return select(self.model_class).where(
            or_(
                cast(self.model_class.name, String).ilike(f"%{fuzzy_id}%"),
                cast(self.model_class.id, String).ilike(f"{fuzzy_id}%"),
            )
        )

    def _get_all(self, *relationships) -> list[TSQLModel]:
        with self._engine.new_session() as session:
            stmt = select(self.model_class)
            for rel in relationships:
                stmt = stmt.options(selectinload(rel))
            return session.exec(stmt).all()

    def _get_exact(self, name: str, *relationships) -> Optional[TSQLModel]:
        with self._engine.new_session() as session:
            stmt = select(self.model_class).where(
                self.model_class.name == name
            )
            for rel in relationships:
                stmt = stmt.options(selectinload(rel))
            results = session.exec(stmt.limit(2)).all()
            if len(results) > 1:
                raise ServiceCmdError(f'Multiple results for name "{name}"')
            return results[0] if results else None

    def _get_multi(self, fuzzy_id: str | UUID, *relationships) -> list[TSQLModel]:
        """
        Search by partial/full id or partial/full name match. The partial must match the
        beginning of the comparison string. Case-insensitive.
        """
        with self._engine.new_session() as session:
            stmt = self._make_get_stmt(fuzzy_id)
            for rel in relationships:
                stmt = stmt.options(selectinload(rel))

            result = session.exec(stmt)
            if hasattr(result, 'scalars'):
                return result.scalars().all()
            else:
                return result.all()

    def _get_one(self, fuzzy_id: str | UUID, *relationships) -> TSQLModel:
        results = self._get_multi(fuzzy_id, *relationships)
        if not results:
            raise ServiceCmdError(f'No results for "{fuzzy_id}" in the '
                                  f'"{self.model_class.__tablename__}" table.')
        elif len(results) > 1:
            raise ServiceCmdError(f'Multiple results for "{fuzzy_id}" in the'
                                  f'"{self.model_class.__tablename__} table.')
        return results[0]

    def remove(self, fuzzy_id: str | UUID):
        to_remove = self._get_one(fuzzy_id)
        with self._engine.new_session() as sess:
            sess.delete(to_remove)
            sess.commit()

    def upsert(self, model: TSQLModel, update_fields: Optional[dict] = None) -> TSQLModel:
        try:
            existing = self._get_one(model.id)
        except ServiceCmdError:
            existing = None

        if existing:
            # Update
            if update_fields:
                for key, value in update_fields.items():
                    setattr(existing, key, value)

            with self._engine.new_session() as session:
                session.add(existing)  # ensures SQLModel tracks it
                session.commit()
                session.refresh(existing)
                return existing
        else:
            # Insert
            with self._engine.new_session() as session:
                session.add(model)
                session.commit()
                session.refresh(model)
                return model

TLink = TypeVar('TLink', bound='BaseLink')
TLinkEngine = TypeVar('TLinkEngine', bound='BaseLinkEngine')

class BaseLink(SQLModel):
    """
    Base class for link tables between two entities.
    Concrete subclasses set left_id and right_id fields as UUIDs.
    """
    left_id: UUID
    right_id: UUID

class BaseLinkEngine(Generic[TLink], ABC):
    model_class: Type[TLink]

    def __init__(self, engine: 'DBEngine'):
        self._engine = engine

    def get(self, left_id: UUID, right_id: UUID) -> Optional[TLink]:
        """Return the link object for exact left_id and right_id, or None if missing."""
        with self._engine.new_session() as session:
            stmt = (
                select(self.model_class)
                .where(self.model_class.left_id == left_id)
                .where(self.model_class.right_id == right_id)
            )
            return session.exec(stmt).first()

    def add(self, left_id: UUID, right_id: UUID):
        """Add a link if it does not already exist."""
        if self.get(left_id, right_id):
            return  # already exists

        link = self.model_class(left_id=left_id, right_id=right_id)
        with self._engine.new_session() as session:
            session.add(link)
            session.commit()

    def remove(self, left_id: UUID, right_id: UUID):
        """Remove a link if it exists."""
        link = self.get(left_id, right_id)
        if not link:
            return  # nothing to remove
        with self._engine.new_session() as session:
            session.delete(link)
            session.commit()

TSortedTable = TypeVar('TSortedTable')

class SortedTable(Generic[TSortedTable]):

    @classmethod
    def table_name(cls):
        return cls.__name__

    def __init__(self, elements: list[TSortedTable] = None):
        self._rows: list[TSortedTable] = elements if elements is not None else []
        self.sort()

    def append(self, item: TSortedTable):
        self._rows.append(item)

    def sort(self, reverse: bool = False):
        """Sort items in place by name (case-insensitive)."""
        self._rows.sort(key=lambda x: x.name, reverse=reverse)

    def __getitem__(self, index):
        return self._rows[index]

    def __len__(self):
        return len(self._rows)

    def __iter__(self) -> Iterator[TSortedTable]:
        return iter(self._rows)
