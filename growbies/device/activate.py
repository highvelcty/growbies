from typing import Optional

from growbies.db.engine import db_engine
from growbies.models.service.cmd import DeviceActivateCmd, DeviceDeactivateCmd
from growbies.models.service.resp import ErrorResp
from growbies.session import Session2
from growbies.utils.types import Serial_t

def _match_serials(*tgt_serials: Serial_t) -> ErrorResp | tuple[Serial_t, ...]:
    existing_serials = db_engine.devices.get_all_serials()
    match_serials = {tgt: '' for tgt in tgt_serials}

    for tgt in match_serials:
        for existing_serial in existing_serials:
            if tgt in existing_serial:
                if match_serials[tgt]:
                    return ErrorResp(msg=f'Multiple hits for "{tgt}".')
                match_serials[tgt] = existing_serial

    for tgt, found in match_serials.items():
        if not found:
            return ErrorResp(msg=f'"{tgt}" not found.')

    return tuple(match_serials.values())

def activate(cmd: DeviceActivateCmd, sess: Session2) -> Optional[ErrorResp]:
    serials_or_resp = _match_serials(*cmd.serials)
    if isinstance(serials_or_resp, ErrorResp):
        return serials_or_resp

    serials = serials_or_resp
    db_engine.devices.activate(*serials)
    return None

def deactivate(cmd: DeviceDeactivateCmd, sess: Session2):
    serials_or_resp = _match_serials(*cmd.serials)
    if isinstance(serials_or_resp, ErrorResp):
        return serials_or_resp

    serials = serials_or_resp
    db_engine.devices.deactivate(*serials)
    return None
