from growbies.service.cli import serials_to_devices
from growbies.service.cmd.structs import LoopbackServiceCmd
from growbies.service.resp.structs import ServiceCmdError
from growbies.intf.cmd import LoopbackDeviceCmd
from growbies.intf.resp import VoidDeviceResp
from growbies.worker.pool import get_pool

from argparse import ArgumentParser

from .common import PositionalParam

def make(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))


class LoopbackServiceCmd(BaseServiceCmd):
    serial: Serial_t
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.LOOPBACK, **kw)

def loopback(cmd: LoopbackServiceCmd) -> VoidDeviceResp:
    """
    raises:
        :class:`ServiceCmdError`
        :class:`DeviceError`
    """

    pool = get_pool()
    device = serials_to_devices(cmd.serial)[0]

    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{cmd.serial}" is inactive.')

    return worker.cmd(LoopbackDeviceCmd())
