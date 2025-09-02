from argparse import ArgumentParser, RawDescriptionHelpFormatter
from enum import StrEnum
import logging
import os
import shlex
import sys

from . import __doc__ as pkg_doc
from . import cfg, db, human_input, monitor, plot, sample, service
from .constants import USERNAME
from .utils.privileges import drop_privileges
from growbies.constants import DEFAULT_CMD_TIMEOUT_SECONDS
from growbies.intf.resp import DeviceError
from growbies.service.cmd.structs import *
from growbies.service.resp.structs import ServiceCmdError
from growbies.service.queue import IDQueue, ServiceQueue

CMD = 'cmd'

logger = logging.getLogger(__name__)

class Param:
    KEEP_PRIVILEGES = 'keep_privileges'

class PositionalParam(StrEnum):
    SERIAL = 'serial'
    SERIALS = 'serials'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'PositionalParam') -> str:
        if sub_cmd_ == cls.SERIAL:
            return 'The serial number of a device.'
        elif sub_cmd_ == cls.SERIALS:
            return 'A list of serial numbers. This can be unique partial matches.'
        raise ValueError(f'"{sub_cmd_} does not exist.')

parser = ArgumentParser(description=pkg_doc, formatter_class=RawDescriptionHelpFormatter)
parsers = {CMD: parser}
parser_adder = parser.add_subparsers(dest=CMD, required=True)

for pkg in (cfg, db, human_input, monitor, plot, sample, service):
    parser_adder.add_parser(pkg.__name__.split('.')[-1], help=pkg.__doc__, add_help=False)
for cmd in ServiceCmd.external_cmds:
    parsers[cmd] = parser_adder.add_parser(cmd, help=ServiceCmd.get_help_str(cmd))

parser.add_argument(f'--{Param.KEEP_PRIVILEGES}', default=False, action='store_true',
                    help=f'By default, if the program is executed with root privileges, these will '
                         f'be dropped by switching to the "{USERNAME}" user. This is typically '
                         f'only seto to False during package installation work.')

# Activate and Deactivate
for sub_parser in (parsers[ServiceCmd.ACTIVATE], parsers[ServiceCmd.DEACTIVATE]):
    sub_parser.add_argument(PositionalParam.SERIALS, nargs='+', type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIALS))

for sub_parser in (parsers[ServiceCmd.LOOPBACK], parsers[ServiceCmd.ID]):
    sub_parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))

ns, args = parser.parse_known_args(sys.argv[1:])

if not getattr(ns, Param.KEEP_PRIVILEGES):
    drop_privileges()
delattr(ns, Param.KEEP_PRIVILEGES)

cmd: ServiceCmd.type_ = getattr(ns, CMD)

def _run_cmd(cmd_: TBaseServiceCmd, timeout = DEFAULT_CMD_TIMEOUT_SECONDS):
    with ServiceQueue() as cmd_q, IDQueue() as resp_q:
        cmd_.qid = resp_q.qid
        cmd_q.put(cmd_)
        try:
            resp = next(resp_q.get_w_timeout(timeout=timeout))
        except StopIteration:
            resp = ServiceCmdError(f'Command {cmd_.cmd} timeout of {timeout} seconds.')

    if isinstance(resp, (ServiceCmdError, DeviceError)):
        sys.stderr.write(f'{resp}\n')
        sys.exit(getattr(resp, 'error', 1))
    return resp

if ServiceCmd.LS == cmd:
    print(_run_cmd(LsServiceCmd()))
elif ServiceCmd.ACTIVATE == cmd:
    _run_cmd(ActivateServiceCmd(serials=getattr(ns, PositionalParam.SERIALS)))
elif ServiceCmd.DEACTIVATE == cmd:
    _run_cmd(DeactivateServiceCmd(serials=getattr(ns, PositionalParam.SERIALS)))
elif ServiceCmd.LOOPBACK == cmd:
    _run_cmd(LoopbackServiceCmd(serial=getattr(ns, PositionalParam.SERIAL)))
elif ServiceCmd.ID == cmd:
    print(_run_cmd(GetIdServiceCmd(serial=getattr(ns, PositionalParam.SERIAL))))
else:
    fwd_cmd = shlex.split(f'{sys.executable} -m {__package__}.{getattr(ns, CMD)} ') + args
    os.execvp(sys.executable, fwd_cmd)
