from enum import IntFlag
from typing import Optional, TYPE_CHECKING
import logging
import uuid

from prettytable import PrettyTable
from sqlalchemy import cast, Column, Integer, ForeignKey, or_, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, Relationship

from .common import BaseTable, BaseNamedTableEngine, SortedTable
from .gateway import Gateway
from .link import SessionDeviceLink
if TYPE_CHECKING:
    from .session import Session
from growbies.common.utils.report import format_8bit_binary, short_uuid
from growbies.common.utils.types import Serial_t
from growbies.service.common import NoResultsServiceCmdError, MultipleResultsServiceCmdError

logger = logging.getLogger(__name__)

class ConnectionState(IntFlag):
    INITIAL     = 0x00
    ACTIVE      = 0x02

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

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(default='')
    gateway: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey(
                f'{Gateway.__tablename__}.{Gateway.Key.ID}',
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
        back_populates='devices',
        link_model=SessionDeviceLink
    )

    def __init__(self, **data):
        super().__init__(**data)
        if not self.name:
            self.name = str(self.id)

    def has_same_discovery_info(self, other: 'Device') -> bool:
        return (
                self.serial == other.serial
                and self.vid == other.vid
                and self.pid == other.pid
                and self.path == other.path
        )

    def is_active(self) -> bool:
        return bool(self.state & ConnectionState.ACTIVE)

    def __str__(self):
        return (f'{self.name} {self.serial} '
                f'{hex(self.vid)}:{hex(self.pid)} {hex(self.state)} {self.path}')

class Devices(SortedTable[Device]):
    def get(self, fuzzy_id: str | UUID) -> Device:
        fuzzy_id = str(fuzzy_id).lower()

        matches = [
            device
            for device in self._rows
            if (
                    str(device.id).lower().startswith(fuzzy_id)
                    or str(device.serial).lower().startswith(fuzzy_id)
                    or fuzzy_id in device.name.lower()
            )
        ]

        if not matches:
            raise NoResultsServiceCmdError(
                f'No results for "{fuzzy_id}".'
            )
        elif len(matches) > 1:
            raise MultipleResultsServiceCmdError(
                f'Multiple results for "{fuzzy_id}".'
            )

        return matches[0]

    def have_same_discovery_info(self, other: 'Devices') -> bool:
        if not isinstance(other, Devices):
            return False

        if len(self._rows) != len(other._rows):
            return False

        other_by_serial = {
            device.serial: device
            for device in other._rows
        }

        for device in self._rows:
            other_device = other_by_serial.get(device.serial)

            if other_device is None:
                return False

            if not device.has_same_discovery_info(other_device):
                return False

        return True

    def __str__(self):
        table = PrettyTable((Device.Key.ID, Device.Key.NAME, Device.Key.SERIAL, Device.Key.STATE,
                             f'{Device.Key.VID}:{Device.Key.PID}', Device.Key.PATH),
                            title=self.table_name())
        for device in self._rows:
            if device.name == str(device.id):
                device_name = short_uuid(device.name)
            else:
                device_name = device.name
            table.add_row([short_uuid(device.id), device_name, device.serial,
                           f'{format_8bit_binary(device.state)}',
                           f'{device.vid:04x}:{device.pid:04x}',
                           device.path])
        return str(table)

class DeviceEngine(BaseNamedTableEngine):
    model_class = Device

    def get(self, fuzzy_id: str | UUID) -> Device:
        return self._get_one(fuzzy_id, Device.gateways, Device.sessions)

    def list(self) -> Devices:
        return Devices(self._get_all())

    def merge_with_discovered(self, discovered_devices: Devices) -> Devices:
        existing_devices = self.list()
        existing_by_serial = {
            device.serial: device
            for device in existing_devices
        }
        merged_by_serial = {}

        for discovered in discovered_devices:
            existing = existing_by_serial.get(discovered.serial)

            if existing is None:
                # Newly discovered devices start in initial state
                discovered.state = ConnectionState.INITIAL
                self.upsert(discovered)
                merged_by_serial[discovered.serial] = discovered
                continue

            self.upsert(existing, {
                Device.Key.GATEWAY: discovered.gateway,
                Device.Key.PATH: discovered.path,
            })
            merged_by_serial[discovered.serial] = existing

        return Devices(elements=[
            merged_by_serial[device.serial]
            for device in discovered_devices
        ])

    def upsert(self, model: Device, fields: Optional[dict] = None) -> Device:
        if fields is None:
            fields = {
                Device.Key.NAME: model.name,
                Device.Key.STATE: model.state,
            }
        return super().upsert(model, fields)

    def clear_active(self, id_: UUID):
        existing = self.get(id_)
        existing.state &= ~ConnectionState.ACTIVE
        self.upsert(existing)

    def set_active(self, id_: UUID):
        existing = self.get(id_)
        existing.state |= ConnectionState.ACTIVE
        self.upsert(existing)
