import re
import logging
import shlex
import subprocess

from growbies.models.db import Device, Devices, ConnectionState
from growbies.db.engine import db_engine
from growbies.session import Session2
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)

class SupportedVidPid:
    ESPRESSIF_DEBUG = (0x303a, 0x1001)
    FTDI_FT232 = (0x0403, 0x6001)

    all_ = (ESPRESSIF_DEBUG, FTDI_FT232)


def ls(session: Session2) -> Devices:
    discovered_devices = Devices()
    _discover_info(discovered_devices, session)
    return db_engine.devices.merge_with_discovered(discovered_devices)

def _discover_info(devices: Devices, session: Session2):
    vid_re = re.compile(r'.*idVendor.*==\"([0-9a-fA-F]+)\"')
    pid_re = re.compile(r'.*idProduct.*==\"([0-9a-fA-F]+)\"')
    serial_re = re.compile(r'.*serial.*==\"([^\"]+)\"')

    paths = list(InstallPaths.DEV.value.glob('ttyUSB*'))
    paths.extend(InstallPaths.DEV.value.glob('ttyACM*'))

    for path in paths:
        cmd = f'udevadm info --attribute-walk --no-pager {path}'
        try:
            proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, check=True, encoding='utf-8')
        except subprocess.CalledProcessError as err:
            logger.error(err.stderr)
            logger.exception(err)
            continue

        vid = None
        pid = None
        serial = None

        for line in proc.stdout.splitlines():
            vid_search = vid_re.search(line)
            if vid_search:
                vid = int(vid_search.group(1), 16)
            pid_search = pid_re.search(line)

            if pid_search:
                pid = int(pid_search.group(1), 16)

            if (vid, pid) in SupportedVidPid.all_:
                serial_search = serial_re.search(line)
                if serial_search:
                    serial = serial_search.group(1)
                    break

        if serial:
            devices.append(Device(gateway=session.gateway.id, vid=vid, pid=pid, serial=serial,
                                  path=str(path), state=ConnectionState.DISCOVERED))
