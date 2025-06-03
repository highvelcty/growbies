from pathlib import Path
from typing import Iterator
import shlex
import subprocess

FTDI_USB_VENDOR_ID = 0x0403
FTDI_232R_USB_PRODUCT_ID = 0x6001

def get_usb_paths() -> Iterator[Path]:
    cmd = 'lsusb -d %X:%X' % (FTDI_USB_VENDOR_ID, FTDI_232R_USB_PRODUCT_ID)
    proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, check=True, encoding='utf-8')
    for line in proc.stdout.splitlines():
        bus_str, bus, device_str, device = line.split(':')[0].split()
        if bus_str.lower() == 'bus' and device_str.lower() == 'device':
            yield Path(f'/dev/bus/usb/{bus}/{device}')
