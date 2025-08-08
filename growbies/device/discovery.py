from typing import Optional, Iterator
import shlex
import subprocess

from prettytable import PrettyTable
from pydantic import BaseModel

from growbies.utils.paths import InstallPaths

class SupportedVidPid:
    ESPRESSIF_DEBUG = (0x303a, 0x1001)
    FTDI_FT232 = (0x0403, 0x6001)

    all_ = (ESPRESSIF_DEBUG, FTDI_FT232)

class UsbDevice(BaseModel):
    vid: int
    pid: int
    serial: str
    path: Optional[str] = None

    def __str__(self):
        return f'{self.path} {self.serial} {hex(self.vid)}:{hex(self.pid)}'

class UsbDevices(BaseModel):
    devices: list[UsbDevice] = list()

    def append(self, device: UsbDevice):
        self.devices.append(device)

    def __getitem__(self, index):
        return self.devices[index]

    def __len__(self):
        return len(self.devices)

    def __iter__(self) -> Iterator[UsbDevice]:
        return iter(self.devices)

    def __str__(self):
        table = PrettyTable(('Path', 'Serial', 'VID:PID'))
        for device in self.devices:
            table.add_row([device.path, device.serial,
                           f'{device.vid:04x}:{device.pid:04x}'])
        return str(table)

def _get_udevadm_info(devices: UsbDevices):
    paths = InstallPaths.DEV.value.glob('tty*')
    cmd = 'udevadm info --no-pager'
    split_cmd = shlex.split(cmd) + [str(path) for path in paths]
    proc = subprocess.run(split_cmd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True, encoding='utf-8')

    devname = None
    for line in proc.stdout.splitlines():
        if 'DEVNAME=' in line:
            devname = line.split('=')[-1]
        if 'ID_USB_SERIAL_SHORT=' in line:
            serial = line.split('=')[-1]
            for device in devices:
                if serial == device.serial:
                    device.path = devname

def _get_vid_pid_serial(devices: UsbDevices):
    for path in InstallPaths.SYS_BUS_USB_DEVICES.value.iterdir():
        path_to_vid = path / 'idVendor'
        path_to_pid = path / 'idProduct'
        path_to_serial = path / 'serial'
        if path_to_vid.exists() and path_to_pid.exists() and path_to_serial.exists():
            vid = int(path_to_vid.read_text(), 16)
            pid = int(path_to_pid.read_text(), 16)
            serial = path_to_serial.read_text().strip()
            if (vid, pid) in SupportedVidPid.all_:
                devices.append(UsbDevice(vid=vid, pid=pid, serial=serial))

def discover_usb() -> UsbDevices:
    devices = UsbDevices()
    _get_vid_pid_serial(devices)
    _get_udevadm_info(devices)
    return devices
