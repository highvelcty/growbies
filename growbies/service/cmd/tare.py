import argparse
from argparse import ArgumentParser
from typing import Optional
import logging

from ..common import ServiceCmd, PositionalParam, ServiceCmdError
from ..serials_to_devices import serials_to_devices
from growbies.device.common import tare as tare_mod
from growbies.device.common import internal_to_external_field
from growbies.device.cmd import GetTareDeviceCmd, SetTareDeviceCmd
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

class Param:
    INIT = 'init'

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
    parser.add_argument(
        f'--{internal_to_external_field(tare_mod.Tare.Field.VALUES)}',
        action = 'append',
        default = argparse.SUPPRESS,
        metavar = ('TARE (IDX)', 'VALUE'),
        nargs = 2,
        type = float,
        help = f'Set tare for a given index. The length of the tare list is '
               f'{tare_mod.Tare.TARE_COUNT}.'
    )

def _init(worker):
    cmd = SetTareDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[tare_mod.Tare]:
    pool = get_pool()
    serial = cmd.kw.pop(PositionalParam.SERIAL)
    init = cmd.kw.pop(Param.INIT)
    device = serials_to_devices(serial)[0]
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    if init:
        _init(worker)
        return None

    tare: tare_mod.Tare = worker.cmd(GetTareDeviceCmd())

    if all(value is None for value in cmd.kw.values()):
        return tare

    tare_list = cmd.kw.pop(internal_to_external_field(tare.Field.VALUES), list())
    existing = tare.values
    for idx, val in tare_list:
        try:
            existing[int(idx)] = val
        except IndexError:
            raise ServiceCmdError(
                f'Index out of range, length of tare array is {tare_mod.Tare.TARE_COUNT}.')
    tare.values = existing

    cmd = SetTareDeviceCmd(tare = tare)

    _ = worker.cmd(cmd)
    return None
