from typing import Optional
import logging

from .discovery import ls
from growbies.db.engine import db_engine
from growbies.models.service.cmd import DeviceActivateCmd, DeviceDeactivateCmd
from growbies.models.service.resp import ErrorResp
from growbies.session import Session2
from growbies.utils.types import Serial_t

logger = logging.getLogger(__name__)

def _match_serials(*tgt_serials: Serial_t, sess: Session2) -> ErrorResp | tuple[Serial_t, ...]:
    devices = ls(sess)
    existing_serials = [dev.serial for dev in devices]
    match_serials = {tgt: '' for tgt in tgt_serials}

    for tgt in match_serials:
        for existing_serial in existing_serials:
            if tgt.lower() in existing_serial.lower():
                if match_serials[tgt]:
                    return ErrorResp(msg=f'Multiple hits for "{tgt}".')
                match_serials[tgt] = existing_serial

    for tgt, found in match_serials.items():
        if not found:
            return ErrorResp(msg=f'"{tgt}" not found.')

    return tuple(match_serials.values())

def _de_activate(cmd: DeviceActivateCmd | DeviceDeactivateCmd, sess: Session2):
    serials_or_resp = _match_serials(*cmd.serials, sess=sess)
    if isinstance(serials_or_resp, ErrorResp):
        return serials_or_resp

    serials = serials_or_resp
    if isinstance(cmd, DeviceActivateCmd):
        db_engine.devices.activate(*serials)
    else:
        db_engine.devices.deactivate(*serials)
    return None

def activate(cmd: DeviceActivateCmd, sess: Session2) -> Optional[ErrorResp]:
    return _de_activate(cmd, sess)


def deactivate(cmd: DeviceDeactivateCmd, sess: Session2):
    return _de_activate(cmd, sess)
