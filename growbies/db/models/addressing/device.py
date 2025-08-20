from enum import IntFlag
from typing import Iterator, Optional, TYPE_CHECKING

from prettytable import PrettyTable
from pydantic import BaseModel
from pydantic.fields import ComputedFieldInfo
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, Integer, ForeignKey, String

from .base import KeyStr
from .gateway import Gateway
if TYPE_CHECKING:
    from .endpoint import Endpoint
from growbies.utils.types import Serial_t, DeviceID_t
from growbies.utils.report import format_8bit_binary


class ConnectionState(IntFlag):
    INITIAL     = 0x00
    DISCOVERED  = 0x01
    ACTIVE      = 0x02
    CONNECTED   = 0x04
    ERROR       = 0x08

class Device(SQLModel, table=True):
    class Key:
        ID: KeyStr = 'id'
        NAME: KeyStr = 'name'
        GATEWAY: KeyStr = 'gateway'
        SERIAL: KeyStr = 'serial'
        VID: KeyStr = 'vid'
        PID: KeyStr = 'pid'
        PATH: KeyStr = 'path'
        STATE: KeyStr = 'state'

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
    endpoints: list['Endpoint'] = Relationship(back_populates='device_relation',
                                               cascade_delete=True)

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
