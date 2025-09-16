from argparse import ArgumentParser
import logging

from ..common import ServiceCmd, PositionalParam, ServiceCmdError
from ..serials_to_devices import serials_to_devices
from growbies.device.common.read import DataPoint
from growbies.device.cmd import ReadDeviceCmd
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

class Param:
    TIMES = 'times'
    RAW = 'raw'

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))
    parser.add_argument(f'--{Param.TIMES}', type=int, nargs='?',
                        default=ReadDeviceCmd.DEFAULT_TIMES,
                        help='The number of samples to take for the read operations')
    parser.add_argument(f'--{Param.RAW}', action='store_true',
                        help='Read raw, uncorrected/calibrated values.')

def execute(cmd: ServiceCmd) -> DataPoint:
    pool = get_pool()
    serial = cmd.kw.pop(PositionalParam.SERIAL)
    raw = cmd.kw.pop(Param.RAW)
    times = cmd.kw.pop(Param.TIMES)

    device = serials_to_devices(serial)[0]
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    return worker.cmd(ReadDeviceCmd(raw=raw, times=times))
