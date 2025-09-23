from enum import IntFlag
from typing import Iterator, Optional, TYPE_CHECKING

from prettytable import PrettyTable
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel import Session as DBSession
from sqlalchemy import Column, Integer, ForeignKey, String, select

from .gateway import Gateway
from .session import Session, SessionDeviceLink
if TYPE_CHECKING:
    from growbies.db.engine import DBEngine
from growbies.utils.report import format_8bit_binary
from growbies.utils.types import Serial_t, DeviceID_t, SerialOrDeviceID_t

class ConnectionState(IntFlag):
    INITIAL     = 0x00
    DISCOVERED  = 0x01
    ACTIVE      = 0x02
    CONNECTED   = 0x04
    ERROR       = 0x08

class Device(SQLModel, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'
        GATEWAY = 'gateway'
        SERIAL = 'serial'
        VID = 'vid'
        PID = 'pid'
        PATH = 'path'
        STATE = 'state'

    id: DeviceID_t = Field(default=None, primary_key=True)
    name: str = 'Default'
    gateway: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey(
                f'{Gateway.__tablename__}.id',
                ondelete="CASCADE"
            ),
            nullable =False
        )
    )
    serial: Serial_t = Field(sa_column=Column(String, unique=True, index=True))
    vid: int
    pid: int
    path: Optional[str]
    state: ConnectionState = \
        Field(sa_column=Column(Integer, nullable=False, default=ConnectionState.INITIAL))

    gateway_relation: Gateway = Relationship(back_populates='devices')
    active_sessions: list[Session] = Relationship(
        back_populates="active_devices",
        link_model=SessionDeviceLink
    )

    def init_discovery_info(self):
        self.state &= ~ConnectionState.DISCOVERED
        self.path = None

    def init_start_connection(self):
        self.state &= ~ConnectionState.ERROR
        self.state &= ~ConnectionState.CONNECTED

    def is_initial(self) -> bool:
        return bool(not self.state)

    def is_discovered(self) -> bool:
        return bool(self.state & ConnectionState.DISCOVERED)

    def is_active(self) -> bool:
        return bool(self.state & ConnectionState.ACTIVE)

    def is_connected(self) -> bool:
        return bool(self.state & ConnectionState.CONNECTED)

    def is_error(self) -> bool:
        return bool(self.state & ConnectionState.ERROR)

    def __str__(self):
        return (f'{self.name} {self.serial} '
                f'{hex(self.vid)}:{hex(self.pid)} {hex(self.state)} {self.path}')


class Devices(BaseModel):
    devices: list[Device] = Field(default_factory=list)

    def get(self, serial) -> Optional[Device]:
        for dev in self.devices:
            if dev.serial == serial:
                return dev
        return None

    def append(self, device: Device):
        self.devices.append(device)

    def __getitem__(self, index):
        return self.devices[index]

    def __len__(self):
        return len(self.devices)

    def __iter__(self) -> Iterator[Device]:
        return iter(self.devices)

    def sort(self) -> 'Devices':
        return Devices(devices=sorted(self.devices, key=lambda d: d.serial))

    def __str__(self):
        table = PrettyTable(('Name', 'Serial', 'VID:PID', 'State', 'Path'))
        for device in self.sort():
            table.add_row([device.name, device.serial,
                           f'{device.vid:04x}:{device.pid:04x}',
                           f'{format_8bit_binary(device.state)}', device.path])
        return str(table)

class DevicesEngine:
    def __init__(self, engine: 'DBEngine'):
        self._engine = engine

    def merge_with_discovered(self, discovered_devices: Devices) -> Devices:
        with self._engine.new_session() as db_session, db_session.begin():
            merged_devices = self._merge_with_discovered(discovered_devices, db_session)
            for device in merged_devices:
                self._overwrite(device, db_session)
            return Devices(devices=[dev.model_copy() for dev in merged_devices])

    def set_active(self, *serials_or_ids: SerialOrDeviceID_t):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(*serials_or_ids, flag=ConnectionState.ACTIVE, value=True,
                           db_session=db_session)

    def clear_active(self, *serials_or_ids: Serial_t):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(*serials_or_ids, flag=ConnectionState.ACTIVE, value=False,
                           db_session=db_session)

    def get(self, serial_or_id: SerialOrDeviceID_t) -> Device:
        with self._engine.new_session() as db_session:
            return self._get(serial_or_id, db_session).model_copy()

    def get_engine(self, device_id: DeviceID_t) -> 'DeviceEngine':
        return DeviceEngine(self._engine, device_id)

    @staticmethod
    def _get(serial_or_id: SerialOrDeviceID_t, db_session: DBSession) -> Device:
        if isinstance(serial_or_id, str):
            stmt = select(Device).where(Device.serial == serial_or_id)
        else:
            stmt = select(Device).where(Device.id == serial_or_id)
        # noinspection PyTypeChecker
        return db_session.exec(stmt).scalars().first()

    @staticmethod
    def _get_all(db_session: DBSession) -> Devices:
        stmt = select(Device)
        results = db_session.exec(stmt).scalars().all()
        return Devices(devices=list(results))

    def _merge_with_discovered(self, discovered_devices: Devices, db_session: DBSession) -> Devices:
        merged_devices = self._get_all(db_session)

        # Update existing in DB.
        for existing_device in merged_devices:
            existing_device.init_discovery_info()
            discovered_device = discovered_devices.get(existing_device.serial)
            if discovered_device is not None:
                existing_device.gateway = discovered_device.gateway
                existing_device.serial = discovered_device.serial
                existing_device.vid = discovered_device.vid
                existing_device.pid = discovered_device.pid
                existing_device.path = discovered_device.path
                # Set the bit.
                existing_device.state |= ConnectionState.DISCOVERED

        # Add new
        new_serials = set((dev.serial for dev in discovered_devices))
        existing_serials = set((dev.serial for dev in merged_devices))
        for serial in (new_serials - existing_serials):
            merged_devices.append(discovered_devices.get(serial))

        return merged_devices

    @staticmethod
    def _overwrite(device: Device, db_session: DBSession) -> Device:
        # Lock the row by unique key
        stmt = (
            select(type(device))
            .where(getattr(type(device), Device.Key.NAME) == device.name)
            .with_for_update()
        )
        # Must assign to something to acquire the "with_for_update" lock
        # noinspection PyTypeChecker
        _ = db_session.exec(stmt).scalars().first()
        db_session.add(device)
        db_session.flush()
        db_session.refresh(device)
        return device

    def _set_flag(self, *serials_or_ids: SerialOrDeviceID_t, flag: ConnectionState, value: bool,
                  db_session: DBSession):
        for serial_or_id in serials_or_ids:
            device = self._get(serial_or_id, db_session=db_session)
            if value:
                # set the bit
                device.state |= flag
            else:
                # clear the bit
                device.state &= ~flag

        db_session.flush()

class DeviceEngine:
    def __init__(self, engine: 'DBEngine', device_id: DeviceID_t):
        self._device_id = device_id
        self._engine = engine

    def get(self, serial_or_id: SerialOrDeviceID_t) -> Device:
        with self._engine.new_session() as db_session:
            return self._get(serial_or_id, db_session).model_copy()

    def set_active(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.ACTIVE, value=True, db_session=db_session)

    def clear_active(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.ACTIVE, value=False, db_session=db_session)

    def set_connected(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.CONNECTED, value=True, db_session=db_session)

    def clear_connected(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.CONNECTED, value=False, db_session=db_session)

    def set_error(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.ERROR, value=True, db_session=db_session)

    def clear_error(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.ERROR, value=False, db_session=db_session)

    def init_start_connection(self):
        with self._engine.new_session() as db_session, db_session.begin():
            device = self._get(self._device_id, db_session)
            device.init_start_connection()

    @staticmethod
    def _get(serial_or_device_id: SerialOrDeviceID_t, db_session: DBSession) -> Device:
        if isinstance(serial_or_device_id, str):
            stmt = select(Device).where(Device.serial == serial_or_device_id)
        else:
            stmt = select(Device).where(Device.id == serial_or_device_id)
        # noinspection PyTypeChecker
        return db_session.exec(stmt).scalars().first()

    def _set_flag(self, flag: ConnectionState, value: bool, db_session: DBSession):
        # Attached model
        device = self._get(self._device_id, db_session)
        if value:
            # set the bit
            device.state |= flag
        else:
            # clear the bit
            device.state &= ~flag

        db_session.flush()