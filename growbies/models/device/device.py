from typing import Optional, Iterator

from prettytable import PrettyTable
from pydantic import BaseModel


class SupportedVidPid:
    ESPRESSIF_DEBUG = (0x303a, 0x1001)
    FTDI_FT232 = (0x0403, 0x6001)

    all_ = (ESPRESSIF_DEBUG, FTDI_FT232)

class Device(BaseModel):
    vid: int
    pid: int
    serial: str
    path: Optional[str] = None

    def __str__(self):
        return f'{self.path} {self.serial} {hex(self.vid)}:{hex(self.pid)}'

class Devices(BaseModel):
    devices: list[Device] = list()

    def append(self, device: Device):
        self.devices.append(device)

    def __getitem__(self, index):
        return self.devices[index]

    def __len__(self):
        return len(self.devices)

    def __iter__(self) -> Iterator[Device]:
        return iter(self.devices)

    def __str__(self):
        table = PrettyTable(('Path', 'Serial', 'VID:PID'))
        for device in self.devices:
            table.add_row([device.path, device.serial,
                           f'{device.vid:04x}:{device.pid:04x}'])
        return str(table)
