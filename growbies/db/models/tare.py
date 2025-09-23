from sqlmodel import ARRAY, SQLModel, select, Field, Float, UniqueConstraint
from typing import List
from sqlalchemy import Column

from .common import BaseTableEngine
from growbies.utils.types import TareID_t

class Tare(SQLModel, table=True):
    __table_args__ = (UniqueConstraint('values'),)

    id: TareID_t = Field(default=None, primary_key=True)
    values: List[float] = Field(sa_column=Column(ARRAY(Float), nullable=False))

class TareEngine(BaseTableEngine):
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
