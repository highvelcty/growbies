from argparse import ArgumentParser
from typing import Optional
import logging

from ..common import ServiceCmd, PositionalParam, ServiceCmdError
from ..serials_to_devices import serials_to_devices
from growbies.device.common import tare as tare_mod
from growbies.device.cmd import GetTareDeviceCmd, SetTareDeviceCmd
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

class Param:
    INIT = 'init'
    INDEX = 'index'
    VALUE = 'value'

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
    parser.add_argument(Param.INDEX, nargs="?", type=int, help="Tare index to set")
    parser.add_argument(Param.VALUE, nargs="?", type=float, help="Value to set at index")

def _init(worker):
    cmd = SetTareDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[tare_mod.Tare]:
    pool = get_pool()
    serial = cmd.kw.pop(PositionalParam.SERIAL)
    init = cmd.kw.pop(Param.INIT)
    index = cmd.kw.pop(Param.INDEX)
    value = cmd.kw.pop(Param.VALUE)
    if (index is None and value is not None) or (index is not None and value is None):
        raise ServiceCmdError(f'Tare index and value must be provided together.')

    device = serials_to_devices(serial)[0]
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    if init:
        _init(worker)
        return None

    tare: tare_mod.NvmTare = worker.cmd(GetTareDeviceCmd())

    if index is None:
        return tare.payload

    existing = tare.payload.values
    try:
        existing[index] = value
    except IndexError:
        raise ServiceCmdError(
            f'Index out of range, length of tare array is {tare_mod.Tare.TARE_COUNT}.')

    tare.payload.values = existing

    cmd = SetTareDeviceCmd(tare=tare)

    _ = worker.cmd(cmd)
    return None
