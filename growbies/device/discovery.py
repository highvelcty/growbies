import logging
import shlex
import subprocess

from growbies.models.device import Device, Devices
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)

class SupportedVidPid:
    ESPRESSIF_DEBUG = (0x303a, 0x1001)
    FTDI_FT232 = (0x0403, 0x6001)

    all_ = (ESPRESSIF_DEBUG, FTDI_FT232)

def _get_udevadm_info(devices: Devices):
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

def _get_vid_pid_serial(devices: Devices):
    for path in InstallPaths.SYS_BUS_USB_DEVICES.value.iterdir():
        path_to_vid = path / 'idVendor'
        path_to_pid = path / 'idProduct'
        path_to_serial = path / 'serial'
        if path_to_vid.exists() and path_to_pid.exists() and path_to_serial.exists():
            vid = int(path_to_vid.read_text(), 16)
            pid = int(path_to_pid.read_text(), 16)
            serial = path_to_serial.read_text().strip()
            if (vid, pid) in SupportedVidPid.all_:
                devices.append(Device(vid=vid, pid=pid, serial=serial))

def ls() -> Devices:
    devices = Devices()
    _get_vid_pid_serial(devices)
    _get_udevadm_info(devices)
    return devices
