from argparse import ArgumentParser, RawDescriptionHelpFormatter
import logging
import os
import shlex
import sys

from . import __doc__ as pkg_doc
from . import cfg, db, service
from .constants import USERNAME
from .utils.privileges import drop_privileges
from growbies.constants import DEFAULT_CMD_TIMEOUT_SECONDS
from growbies.device.resp import DeviceError
from growbies.service.cmd import activate, identify, loopback, ls
from growbies.service.common import PositionalParam, ServiceCmd, ServiceCmdError, TBaseServiceCmd
from growbies.service.queue import IDQueue, ServiceQueue

CMD = 'cmd'

logger = logging.getLogger(__name__)

class Param:
    KEEP_PRIVILEGES = 'keep_privileges'

parser = ArgumentParser(description=pkg_doc, formatter_class=RawDescriptionHelpFormatter)
parsers = {CMD: parser}
parser_adder = parser.add_subparsers(dest=CMD, required=True)

for pkg in (cfg, db, service):
    parser_adder.add_parser(pkg.__name__.split('.')[-1], help=pkg.__doc__, add_help=False)
for cmd in ServiceCmd:
    help_str = ServiceCmd.get_help_str(cmd)
    desc_str = ServiceCmd.get_description_str(cmd)
    parsers[cmd] = parser_adder.add_parser(cmd, description=desc_str, help=help_str,
                                           formatter_class=RawDescriptionHelpFormatter)

parser.add_argument(f'--{Param.KEEP_PRIVILEGES}', default=False, action='store_true',
                    help=f'By default, if the program is executed with root privileges, these will '
                         f'be dropped by switching to the "{USERNAME}" user. This is typically '
                         f'only seto to False during package installation work.')

activate.make_cli(parsers[ServiceCmd.ACTIVATE])
activate.make_cli(parsers[ServiceCmd.DEACTIVATE])
identify.make_cli(parsers[ServiceCmd.ACTIVATE])
loopback.make_cli(parsers[ServiceCmd.LOOPBACK])

ns, unknown = parser.parse_known_args(sys.argv[1:])
ns_dict = vars(ns)

if not ns_dict.pop(Param.KEEP_PRIVILEGES):
    drop_privileges()

cmd: ServiceCmd = ns_dict.pop(CMD)

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
    print(_run_cmd(ls.LsServiceCmd()))
elif ServiceCmd.ACTIVATE == cmd:
    _run_cmd(activate.ActivateServiceCmd(serials=getattr(ns, PositionalParam.SERIALS)))
elif ServiceCmd.DEACTIVATE == cmd:
    _run_cmd(activate.DeactivateServiceCmd(serials=getattr(ns, PositionalParam.SERIALS)))
elif ServiceCmd.LOOPBACK == cmd:
    _run_cmd(loopback.LoopbackServiceCmd(serial=getattr(ns, PositionalParam.SERIAL)))
elif ServiceCmd.ID == cmd:
    serial = ns_dict.pop(PositionalParam.SERIAL)
    if unknown:
        unknown_str = ', '.join(unknown)
        parsers[ServiceCmd.ID].error(f"Unrecognized arguments: {unknown_str}")
    print(_run_cmd(identify.IdServiceCmd(serial=serial, device_cmd_kw=ns_dict)))
else:
    fwd_cmd = shlex.split(f'{sys.executable} -m {__package__}.{cmd} ') + unknown
    os.execvp(sys.executable, fwd_cmd)

