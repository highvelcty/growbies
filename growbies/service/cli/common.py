from enum import StrEnum

from growbies.db.models import Devices
from growbies.service.cmd import discovery
from growbies.service.resp.structs import ServiceCmdError
from growbies.utils.types import Serial_t

__all__ = ['PositionalParam', 'serials_to_devices']

class PositionalParam(StrEnum):
    SERIAL = 'serial'
    SERIALS = 'serials'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'PositionalParam') -> str:
        if sub_cmd_ == cls.SERIAL:
            return 'The serial number of a device.'
        elif sub_cmd_ == cls.SERIALS:
            return 'A list of serial numbers. This can be unique partial matches.'
        raise ValueError(f'"{sub_cmd_} does not exist.')

def serials_to_devices(*tgt_serials: Serial_t) -> Devices:
    devices = discovery.ls()
    matches = dict()

    for tgt in tgt_serials:
        for device in devices:
        # for serial, device_id in serials_ids.items():
            if tgt.lower() in device.serial.lower():
                if matches.get(tgt):
                    raise ServiceCmdError(f'Multiple hits for "{tgt}".')
                matches[tgt] = device

    for tgt in tgt_serials:
        if tgt not in matches:
            raise ServiceCmdError(f'"{tgt}" not found.')

    return Devices(devices=list(matches.values()))
