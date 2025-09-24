from argparse import ArgumentParser
from typing import Optional
import logging

from ..common import ServiceCmd, PositionalParam, ServiceCmdError
from ..utils import serials_to_devices
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
    parser.add_argument(Param.VALUE, nargs="?", type=float,
                        help="Value to set at index. Input NAN (case insensitive) to omit the "
                             "slot.")

def _init(worker):
    cmd = SetTareDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def execute(cmd: ServiceCmd) -> Optional[tare_mod.Tare]:
    device = serials_to_devices(serial)[0]

