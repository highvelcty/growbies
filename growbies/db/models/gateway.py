from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, Integer, ForeignKey, String, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .account import Account

if TYPE_CHECKING:
    from .device import Device
    from growbies.db.engine import DBEngine

class Gateway(SQLModel, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'
        ACCOUNT = 'account'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column=Column(String, unique=True, index=True))
    account: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Account.__tablename__}.id',
                ondelete="CASCADE"
            ),
            nullable=False
        )
    )

    account_relation: Account = Relationship(back_populates='gateways')
    devices: list['Device'] = Relationship(back_populates='gateway_relation', cascade_delete=True)

class GatewayEngine:
    def __init__(self, engine: 'DBEngine'):
        self._engine = engine

    def upsert(self, gateway: Gateway):
        table = gateway.__table__
        # Get the single primary key column name
        unique_key = Gateway.Key.NAME

        new_values = gateway.model_dump(exclude_unset=True)

        insert_stmt = pg_insert(table).values(new_values)

        # Always exclude the unique key on upsert
        keys_to_exclude = [unique_key]

        # Overwrite everything except the keys to be excluded. The insert_stmt.excluded is not
        # data from the DB, but a special SQL expression construct representing the `EXCLUDED`
        # table alias use in PostgresSQL `ON CONFLICT` clause.
        key_to_update = {k: insert_stmt.excluded[k] for k in new_values if k not in keys_to_exclude}

        # Filter based on
        update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[unique_key],
            set_=key_to_update
        )

        with self._engine.new_session() as session:
            # noinspection PyTypeChecker
            session.exec(update_stmt)
            session.commit()

            stmt = (
                select(Gateway)
                .where(getattr(Gateway, unique_key) == gateway.name)
            )
            return session.exec(stmt).first()
