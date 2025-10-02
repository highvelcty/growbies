import uuid

from sqlmodel import ARRAY, SQLModel, select, Field, Float, UniqueConstraint
from typing import List, Optional

from sqlalchemy import Column

from .common import BaseTable, BaseNamedTableEngine
from growbies.utils.types import TareID_t

class Tare(BaseTable, table=True):
    __table_args__ = (UniqueConstraint('values'),)

    id: Optional[TareID_t] = Field(default_factory=uuid.uuid4, primary_key=True)
    values: List[float] = Field(sa_column=Column(ARRAY(Float), nullable=False))

class TareEngine(BaseNamedTableEngine):
    model_class = Tare

    def insert(self, values: List[float]) -> Tare:
        """
        Insert a new tare row for a given list of floats.
        If an identical row exists, return the existing row.
        Returns the Tare row object.
        """
        stmt = select(Tare).where(Tare.values == values)
        with self._engine.new_session() as session:
            existing = session.exec(stmt).first()
            if existing:
                return existing

            tare_row = Tare(values=values)
            session.add(tare_row)
            session.commit()
            session.refresh(tare_row)
            return tare_row
