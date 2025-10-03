from enum import IntFlag
from typing import Iterator, Optional, TYPE_CHECKING
import logging
import uuid

from prettytable import PrettyTable
from sqlalchemy import cast, Column, Integer, ForeignKey, or_, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, Relationship

from .common import BaseTable, BaseNamedTableEngine
from .gateway import Gateway
from .link import SessionDeviceLink
if TYPE_CHECKING:
    from .session import Session
from growbies.utils.report import format_8bit_binary
from growbies.utils.types import Serial_t, DeviceID_t, GatewayID_t

logger = logging.getLogger(__name__)

class ConnectionState(IntFlag):
    INITIAL     = 0x00
    DISCOVERED  = 0x01
    ACTIVE      = 0x02
    CONNECTED   = 0x04
    ERROR       = 0x08

class Device(BaseTable, table=True):
    class Key:
        ID = 'id'
        NAME = 'name'
        GATEWAY = 'gateway'
        SERIAL = 'serial'
        VID = 'vid'
        PID = 'pid'
        PATH = 'path'
        STATE = 'state'

    id: Optional[DeviceID_t] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(default='Default')
    gateway: GatewayID_t = Field(
        sa_column=Column(
            UUID(as_uuid=True),
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

    gateways: Gateway = Relationship(back_populates='devices')
    sessions: list['Session'] = Relationship(
        back_populates="devices",
        link_model=SessionDeviceLink
    )

    def init_discovery_info(self):
        self.state &= ~ConnectionState.DISCOVERED
        self.path = None

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

class Devices:
    def __init__(self, devices: list[Device] = None):
        if devices is None:
            self._devices = list()
        else:
            self._devices = devices
        self.sort()

    def append(self, device: Device):
        self._devices.append(device)

    def get_by_serial(self, serial: Serial_t) -> Optional[Device]:
        for device in self._devices:
            if device.serial == serial:
                return device
        return None

    def __getitem__(self, index):
        return self._devices[index]

    def __len__(self):
        return len(self._devices)

    def __iter__(self) -> Iterator[Device]:
        return iter(self._devices)

    def sort(self, reverse: bool = False):
        self._devices.sort(key=lambda tag: tag.name.lower(), reverse=reverse)

    def __str__(self):
        table = PrettyTable(('Name', 'Serial', 'VID:PID', 'State', 'Path'))
        for device in self._devices:
            table.add_row([device.name, device.serial,
                           f'{device.vid:04x}:{device.pid:04x}',
                           f'{format_8bit_binary(device.state)}', device.path])
        return str(table)

class DeviceEngine(BaseNamedTableEngine):
    model_class = Device

    def get(self, fuzzy_id: str | UUID) -> Device:
        return self._get_one(fuzzy_id, Device.sessions)

    def init_start_connection(self, id_: UUID):
        existing = self.get(id_)
        existing.state &= ~ConnectionState.ERROR
        existing.state &= ~ConnectionState.CONNECTED
        self.upsert(existing)

    def list(self) -> Devices:
        return Devices(self._get_all(Device.sessions))

    def merge_with_discovered(self, discovered_devices: Devices) -> Devices:
        merged_devices = self._merge_with_discovered(discovered_devices)
        for device in merged_devices:
            self._overwrite(device)
        return Devices(devices=[dev.model_copy() for dev in merged_devices])

    def upsert(self, model: Device, update_fields: Optional[dict] = None) -> Device:
        return super().upsert(model, {Device.Key.NAME: model.name, Device.Key.STATE: model.state})

    def clear_active(self, id_: UUID):
        existing = self.get(id_)
        existing.state &= ~ConnectionState.ACTIVE
        self.upsert(existing)

    def set_active(self, id_: UUID):
        existing = self.get(id_)
        existing.state |= ConnectionState.ACTIVE
        self.upsert(existing)

    def clear_connected(self, id_: UUID):
        existing = self.get(id_)
        existing.state &= ~ConnectionState.CONNECTED
        self.upsert(existing)

    def set_connected(self, id_: UUID):
        existing = self.get(id_)
        existing.state |= ConnectionState.CONNECTED
        self.upsert(existing)

    def clear_error(self, id_: UUID):
        existing = self.get(id_)
        existing.state &= ~ConnectionState.ERROR
        self.upsert(existing)

    def set_error(self, id_: UUID):
        existing = self.get(id_)
        existing.state |= ConnectionState.ERROR
        self.upsert(existing)

    def _make_get_stmt(self, fuzzy_id: str | UUID):
        fuzzy_id  = str(fuzzy_id)
        return select(self.model_class).where(
            or_(
                cast(self.model_class.id, String).ilike(f"{fuzzy_id}%"),
                cast(self.model_class.serial, String).ilike(f"{fuzzy_id}%"),
                cast(self.model_class.name, String).ilike(f"%{fuzzy_id}%"),
            )
        )
    def _merge_with_discovered(self, discovered_devices: Devices) -> Devices:
        merged_devices = self.list()

        # Update existing in DB.
        for existing_device in merged_devices:
            existing_device.init_discovery_info()
            discovered_device = discovered_devices.get_by_serial(existing_device.serial)
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
            merged_devices.append(discovered_devices.get_by_serial(serial))

        return merged_devices

    def _overwrite(self, device: Device) -> Device:
        with self._engine.new_session() as db_sess:
            merged = db_sess.merge(device)  # either updates existing or inserts
            db_sess.commit()  # ensure it persists
            db_sess.refresh(merged)
            return merged
