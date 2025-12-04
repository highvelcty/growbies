from typing import Optional
import logging

from growbies.service.common import ServiceCmd, ServiceCmdError
from growbies.cli.common import Param as CommonParam
from growbies.cli.nvm.identify import Param
from growbies.db.engine import get_db_engine
from growbies.device.cmd import (GetIdentifyDeviceCmd, SetIdentifyDeviceCmd1,
                                 SetIdentifyDeviceCmd2, SetIdentifyDeviceCmd3,
                                 SetIdentifyDeviceCmd4, SetIdentifyDeviceCmd5)
from growbies.device.common.identify import TNvmIdentify
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def _init(worker):
    cmd = SetIdentifyDeviceCmd1(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[TNvmIdentify]:
    engine = get_db_engine()
    pool = get_pool()
    init = cmd.kw.pop(Param.INIT)

    fuzzy_id = cmd.kw.pop(CommonParam.FUZZY_ID, None)
    device = engine.device.get(fuzzy_id)
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    if init:
        _init(worker)
        return None

    ident: TNvmIdentify = worker.cmd(GetIdentifyDeviceCmd())

    if all(value is None for value in cmd.kw.values()):
        return ident

    for key, val in cmd.kw.items():
        if val is not None:
            try:
                getattr(ident.payload, key)
            except AttributeError:
                raise ServiceCmdError(f'Identify version {ident.VERSION} does not support the '
                                      f'"{key}" field.')
            setattr(ident.payload, key, val)

    if ident.hdr.version == SetIdentifyDeviceCmd1.VERSION:
        cmd = SetIdentifyDeviceCmd1()
    elif ident.hdr.version == SetIdentifyDeviceCmd2.VERSION:
        cmd = SetIdentifyDeviceCmd2()
    elif ident.hdr.version == SetIdentifyDeviceCmd3.VERSION:
        cmd = SetIdentifyDeviceCmd3()
    elif ident.hdr.version == SetIdentifyDeviceCmd4.VERSION:
        cmd = SetIdentifyDeviceCmd4()
    elif ident.hdr.version == SetIdentifyDeviceCmd5.VERSION:
        cmd = SetIdentifyDeviceCmd5()
    cmd.identify = ident
    _ = worker.cmd(cmd)
    return None
