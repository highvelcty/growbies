from abc import ABC
from enum import StrEnum
from typing import Any, Generic, Iterator, Optional, TYPE_CHECKING, Type, TypeVar
from uuid import UUID

from sqlalchemy import cast, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.types import String
from sqlmodel import SQLModel, select

if TYPE_CHECKING:
    from growbies.db.engine import DBEngine
from growbies.service.common import (ServiceCmdError, MultipleResultsServiceCmdError,
    NoResultsServiceCmdError)
from growbies.utils.report import short_uuid, TABLE_COLUMN_WIDTH

class BuiltinTagName(StrEnum):
    CALIBRATION = 'calibration'
    READ_ONLY = 'read-only'
    TEMPLATE = 'template'

    @property
    def description(self) -> str:
        if self == self.CALIBRATION:
            return 'A calibration session.'
        elif self == self.READ_ONLY:
            return 'Read-only access. No updating or removal will be permitted with this tag.'
        elif self == self.TEMPLATE:
            return (f'A template from which concrete sessions can be derived. The '
                    f'"{self.READ_ONLY}" tag will automatically be added if it is not already.')
        else:
            return f''

TSQLModel = TypeVar('TSQLModel', bound='BaseTable')

class BaseModel(SQLModel, table=False):
    model_config = dict(arbitrary_types_allowed=True)


class BaseTable(BaseModel, table=False):
    id: Any # This must be overridden.

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
            results = session.exec(stmt).all()
            return results

            # Convert to DTOs
            # Exclude datapoints from DTO conversion
            # meyere
            # return [
            #     self.model_class.model_validate(obj.model_dump(exclude={}))
            #     for obj in results
            # ]

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

            if not results:
                return None
            return results[0]

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
                results = result.scalars().all()
            else:
                results = result.all()

            return results

    def _get_one(self, fuzzy_id: str | UUID, *relationships) -> TSQLModel:
        results = self._get_multi(fuzzy_id, *relationships)
        if not results:
            raise NoResultsServiceCmdError(f'No results for "{fuzzy_id}" in the '
                                           f'"{self.model_class.__tablename__}" table.')
        elif len(results) > 1:
            raise MultipleResultsServiceCmdError(f'Multiple results for "{fuzzy_id}" in the'
                                                 f'"{self.model_class.__tablename__} table.')
        return results[0]

    def remove(self, fuzzy_id: str | UUID):
        to_remove = self._get_one(fuzzy_id)
        with self._engine.new_session() as sess:
            orm = sess.merge(to_remove)
            sess.delete(orm)
            sess.commit()

    def upsert(self, model: TSQLModel, fields: Optional[dict] = None) -> TSQLModel:
        try:
            existing = self._get_one(model.id)
        except ServiceCmdError:
            existing = None

        if existing:
            # Update
            if fields:
                for key, value in fields.items():
                    setattr(existing, key, value)

        with self._engine.new_session() as session:
            orm = session.merge(existing if existing else model)
            session.commit()
            session.refresh(orm)
            return orm

TLink = TypeVar('TLink', bound='BaseLink')
TLinkEngine = TypeVar('TLinkEngine', bound='BaseLinkEngine')

class BaseLink(BaseModel, table=False):
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
            res = session.exec(stmt).first()
            return res if res else None

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
            orm = session.merge(link)
            session.delete(orm)
            session.commit()

TSortedTable = TypeVar('TSortedTable')

class SortedTable(Generic[TSortedTable]):

    @classmethod
    def table_name(cls):
        return cls.__name__

    def __init__(self, elements: list[TSortedTable] = None,
                 max_column_width: int = TABLE_COLUMN_WIDTH):
        self._max_column_width = max_column_width
        self._rows: list[TSortedTable] = elements if elements is not None else []
        self.sort()

    @property
    def max_column_width(self) -> int:
        return self._max_column_width

    @max_column_width.setter
    def max_column_width(self, value):
        self._max_column_width = value

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

