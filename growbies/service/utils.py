from growbies.db.models.device import Devices
from growbies.service.cmd.ls import execute
from growbies.utils.types import Serial_t
from .common import ServiceCmdError

def serials_to_devices(*tgt_serials: Serial_t) -> Devices:
    devices = execute()
    matches = dict()

    for tgt in tgt_serials:
        for device in devices:
            if tgt.lower() in device.serial.lower():
                if matches.get(tgt):
                    raise ServiceCmdError(f'Multiple hits for "{tgt}".')
                matches[tgt] = device

    for tgt in tgt_serials:
        if tgt not in matches:
            raise ServiceCmdError(f'"{tgt}" not found.')

    return Devices(devices=list(matches.values()))