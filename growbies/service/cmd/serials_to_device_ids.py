from growbies.service.resp.structs import ServiceCmdError
from growbies.service.cmd import discovery
from growbies.utils.types import DeviceID_t, Serial_t

def serials_to_device_ids(*tgt_serials: Serial_t) -> tuple[DeviceID_t, ...]:
    devices = discovery.ls()
    serials_ids = {dev.serial: dev.id for dev in devices}
    matches = dict()

    for tgt in tgt_serials:
        for serial, device_id in serials_ids.items():
            if tgt.lower() in serial.lower():
                if matches.get(tgt):
                    raise ServiceCmdError(f'Multiple hits for "{tgt}".')
                matches[tgt] = device_id

    for tgt in tgt_serials:
        if tgt not in matches:
            raise ServiceCmdError(f'"{tgt}" not found.')

    return tuple(matches.values())
