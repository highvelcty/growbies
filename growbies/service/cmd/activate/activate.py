from typing import Optional
import logging

from growbies.service.cmd import discovery
from growbies.db.engine import get_db_engine
from growbies.service.cmd.structs import ActivateCmd, DeactivateCmd
from growbies.service.resp.structs import ErrorResp
from growbies.utils.types import DeviceID_t, Serial_t
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def _match_serials_to_device_ids(*tgt_serials: Serial_t) -> ErrorResp | tuple[DeviceID_t, ...]:
    devices = discovery.ls()
    serials_ids = {dev.serial: dev.id for dev in devices}
    matches = dict()

    for tgt in tgt_serials:
        for serial, device_id in serials_ids.items():
            if tgt.lower() in serial.lower():
                if matches.get(tgt):
                    return ErrorResp(msg=f'Multiple hits for "{tgt}".')
                matches[tgt] = device_id

    for tgt in tgt_serials:
        if tgt not in matches:
            return ErrorResp(msg=f'"{tgt}" not found.')

    return tuple(matches.values())

def activate(cmd: ActivateCmd) -> Optional[ErrorResp]:
    resp = _match_serials_to_device_ids(*cmd.serials)
    if isinstance(resp, ErrorResp):
        return resp

    device_ids = resp
    engine = get_db_engine().devices
    worker_pool = get_pool()

    engine.set_active(*device_ids)
    worker_pool.start(*device_ids)
    return None

def deactivate(cmd: DeactivateCmd) -> Optional[ErrorResp]:
    resp = _match_serials_to_device_ids(*cmd.serials)
    if isinstance(resp, ErrorResp):
        return resp

    device_ids = resp
    engine = get_db_engine().devices
    worker_pool = get_pool()

    engine.clear_active(*device_ids)
    worker_pool.stop(*device_ids)
    worker_pool.wait(*device_ids)
    return None