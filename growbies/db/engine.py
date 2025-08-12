from contextlib import contextmanager

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import create_engine, select, Session, SQLModel

from .constants import SQLMODEL_LOCAL_ADDRESS
from growbies.models.db import Account, Gateway, TSQLModel

class Engine:
    def __init__(self):
        self._lazy_init_engine = None

    @property
    def _engine(self):
        if self._lazy_init_engine is None:
            self._lazy_init_engine = create_engine(SQLMODEL_LOCAL_ADDRESS, echo_pool=True,
                                                   echo=True)
        return self._lazy_init_engine

    def init_tables(self):
        # All models representing tables found in the import space will be created.
        # noinspection PyUnresolvedReferences
        from growbies.models.db import addressing
        with Session(self._engine) as session:
            SQLModel.metadata.create_all(self._engine)
            session.commit()
            session.close()

    def _merge(self, thing):
        with self._new_session() as session:
            merged = session.merge(thing)
            session.commit()
            # To make dynamically created (such as id fields) accessible after session close
            # (detachment)
            session.refresh(merged)
            return merged

    def _upsert(self, instance: TSQLModel) -> TSQLModel:
        table = instance.__table__
        # Get the single primary key column name
        primary_keys = [col.name for col in table.primary_key.columns]
        if len(primary_keys) != 1:
            raise Exception("Composite primary keys not supported")
        pk_name = primary_keys[0]

        unique_key = "name"  # adjust if needed

        values = instance.model_dump(exclude_unset=True)

        insert_stmt = pg_insert(table).values(values)
        to_be_updated = {k: insert_stmt.excluded[k] for k in values if k != unique_key}
        if not to_be_updated:
            to_be_updated = values
        update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[unique_key],
            set_={k: insert_stmt.excluded[k] for k in values if k != unique_key}
        )

        with self._new_session() as session:
            # noinspection PyTypeChecker
            session.exec(update_stmt)
            session.commit()

            refreshed = session.get(type(instance), values.get(pk_name))
            return refreshed

    def upsert_account(self, account: Account) -> Account:
        """
        The implementation of account upsert varies from gateway upsert because, at the time of
        this writing, there is only one column in the account table. If/when that changes,
        the same path for upserting the gateway table can be reused.
        """
        with self._new_session() as session:
            statement = select(Account).where(Account.name == account.name)
            # noinspection PyTypeChecker
            existing_account = session.exec(statement).first()

            if existing_account:
                return existing_account
            else:
                session.add(account)
                session.commit()
                session.refresh(account)
            return account

    def upsert_gateway(self, gateway: Gateway) -> Gateway:
        return self._upsert(gateway)

    @contextmanager
    def _new_session(self):
        session = Session(self._engine)
        try:
            yield session
        finally:
            session.close()

# Application global singleton
db_engine = Engine()
