from contextlib import contextmanager
from typing import Iterator
import logging

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import create_engine, select, Session, SQLModel

from .constants import SQLMODEL_LOCAL_ADDRESS
from growbies.models.db import Account, Device, Devices, Gateway
from growbies.utils.types import Serial_t

logger = logging.getLogger(__name__)

class DBEngine:
    def __init__(self):
        self._lazy_init_engine = None
        self.account = AccountEngine(self)
        self.gateway = GatewayEngine(self)
        self.devices = DevicesEngine(self)

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
        with self.new_session() as session:
            merged = session.merge(thing)
            session.commit()
            # To make dynamically created (such as id fields) accessible after session close
            # (detachment)
            session.refresh(merged)
            return merged

    @contextmanager
    def new_session(self):
        session = Session(self._engine)
        try:
            yield session
        finally:
            session.close()

class AccountEngine:
    def __init__(self, engine: DBEngine):
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

class GatewayEngine:
    def __init__(self, engine: DBEngine):
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


class DevicesEngine:
    def __init__(self, engine: DBEngine):
        self._engine = engine

    def get_all(self) -> Devices:
        with self._engine.new_session() as session:
            stmt = select(Device)
            results = session.exec(stmt).all()
        return Devices(devices=list(results))

    def get_all_serials(self) -> Iterator[Serial_t]:
        for device in self.get_all():
            yield device.serial

    def _overwrite(self, device: Device) -> Device:
        with self._engine.new_session() as session:
            session.begin()  # explicitly start a transaction

            # Lock the row by unique key
            stmt = (
                select(type(device))
                .where(getattr(type(device), Device.Key.NAME) == device.name)
                .with_for_update()
            )
            session.exec(stmt)

            session.add(device)
            session.commit()
            session.refresh(device)
            return device

    def _merge_with_new(self, new_devices: Devices) -> Devices:
        merged_devices = self.get_all()

        # Update existing
        for existing_device in merged_devices:
            new_device = new_devices.get(existing_device.serial)
            if new_device is not None:
                existing_device.gateway = new_device.gateway
                existing_device.serial = new_device.serial
                existing_device.vid = new_device.vid
                existing_device.pid = new_device.pid
                existing_device.path = new_device.path
                existing_device.state |= new_device.state

        # Add new
        new_serials = set((dev.serial for dev in new_devices))
        existing_serials = set((dev.serial for dev in merged_devices))
        for serial in (new_serials - existing_serials):
            merged_devices.append(new_devices.get(serial))

        return merged_devices

    def merge_with_new(self, new_devices: Devices):
        merged_devices = self._merge_with_new(new_devices)
        for device in merged_devices:
            self._overwrite(device)
        return merged_devices

    def activate(self, *serials: Serial_t):
        pass

    def deactivate(self, *serials: Serial_t):
        pass

# Application global singleton
db_engine = DBEngine()
