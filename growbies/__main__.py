from argparse import ArgumentParser, RawDescriptionHelpFormatter
import logging
import sys

from . import __doc__ as pkg_doc
from .utils.privileges import drop_privileges
from growbies.constants import DEFAULT_CMD_TIMEOUT_SECONDS
from growbies.device.resp import DeviceError
from growbies.service.cmd import activate, identify, loopback
from growbies.service.common import (CMD, ServiceCmd, ServiceOp, ServiceCmdError, TBaseServiceCmd)
from growbies.service.queue import IDQueue, ServiceQueue

logger = logging.getLogger(__name__)

drop_privileges()

parser = ArgumentParser(description=pkg_doc, formatter_class=RawDescriptionHelpFormatter)
parsers = {CMD: parser}
parser_adder = parser.add_subparsers(dest=CMD, required=True)

for cmd in ServiceOp:
    help_str = ServiceOp.get_help_str(cmd)
    desc_str = ServiceOp.get_description_str(cmd)
    parsers[cmd] = parser_adder.add_parser(cmd, description=desc_str, help=help_str,
                                           formatter_class=RawDescriptionHelpFormatter)

activate.make_cli(parsers[ServiceOp.ACTIVATE])
activate.make_cli(parsers[ServiceOp.DEACTIVATE])
identify.make_cli(parsers[ServiceOp.ID])
loopback.make_cli(parsers[ServiceOp.LOOPBACK])

known, unknown = parser.parse_known_args(sys.argv[1:])
kw = vars(known)
cmd: ServiceOp = kw.pop(CMD)

if unknown:
    parsers[cmd].error(f'Unknown arguments encountered "{unknown}"')

def _run_cmd(cmd_: TBaseServiceCmd, timeout = DEFAULT_CMD_TIMEOUT_SECONDS):
    with ServiceQueue() as cmd_q, IDQueue() as resp_q:
        cmd_.qid = resp_q.qid
        cmd_q.put(cmd_)
        try:
            resp = next(resp_q.get_w_timeout(timeout=timeout))
        except StopIteration:
            resp = ServiceCmdError(f'Command {cmd_.op} timeout of {timeout} seconds.')

    if isinstance(resp, (ServiceCmdError, DeviceError)):
        sys.stderr.write(f'{resp}\n')
        sys.stderr.flush()
        sys.exit(getattr(resp, 'error', 1))
    else:
        if resp is not None:
            print(resp)

_run_cmd(ServiceCmd(op=cmd, kw=kw))
