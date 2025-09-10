from argparse import ArgumentParser, RawDescriptionHelpFormatter
import logging
import sys

from . import __doc__ as pkg_doc
from .utils.privileges import drop_privileges
from growbies.constants import DEFAULT_CMD_TIMEOUT_SECONDS
from growbies.device.resp import DeviceError
from growbies.service.cmd import activate, identify, loopback, ls
from growbies.service.common import (CMD, PositionalParam, ServiceCmd, ServiceCmdError,
                                     TBaseServiceCmd)
from growbies.service.queue import IDQueue, ServiceQueue

logger = logging.getLogger(__name__)

drop_privileges()

parser = ArgumentParser(description=pkg_doc, formatter_class=RawDescriptionHelpFormatter)
parsers = {CMD: parser}
parser_adder = parser.add_subparsers(dest=CMD, required=True)

for cmd in ServiceCmd:
    help_str = ServiceCmd.get_help_str(cmd)
    desc_str = ServiceCmd.get_description_str(cmd)
    parsers[cmd] = parser_adder.add_parser(cmd, description=desc_str, help=help_str,
                                           formatter_class=RawDescriptionHelpFormatter)

activate.make_cli(parsers[ServiceCmd.ACTIVATE])
activate.make_cli(parsers[ServiceCmd.DEACTIVATE])
identify.make_cli(parsers[ServiceCmd.ID])
loopback.make_cli(parsers[ServiceCmd.LOOPBACK])

ns, unknown = parser.parse_known_args(sys.argv[1:])
ns_dict = vars(ns)

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
    if unknown:
        unknown_str = ', '.join(unknown)
        parsers[ServiceCmd.ID].error(f"Unrecognized arguments: {unknown_str}")
    print(_run_cmd(identify.IdServiceCmd(cmd_kw=ns_dict)))
