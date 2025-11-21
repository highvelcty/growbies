from argparse import ArgumentParser, RawDescriptionHelpFormatter
from growbies.cli import (calibration, device, identify, project, read, session, tag, tare, user)
from growbies.cli.common import CMD
from growbies.service.common import ServiceOp
import argcomplete
from . import __doc__ as pkg_doc

"""
This command will evaluate the import time of the CLI tab completion, sorting by cumulative time

python -X importtime -m growbies 2>&1 \
    | awk -F'|' '{cum=$2; gsub(/ /,"",cum); print cum "|" $0}' \
    | sort -nr \
    | cut -d'|' -f2-
"""

parser = ArgumentParser(description=pkg_doc, formatter_class=RawDescriptionHelpFormatter)
parsers = {CMD: parser}
parser_adder = parser.add_subparsers(dest=CMD, required=True)

for cmd in ServiceOp:
    parsers[cmd] = parser_adder.add_parser(cmd, description=cmd.description, help=cmd.help,
                                           formatter_class=RawDescriptionHelpFormatter)

calibration.make_cli(parsers[ServiceOp.CAL])
device.make_cli(parsers[ServiceOp.DEVICE])
identify.make_cli(parsers[ServiceOp.ID])
project.make_cli(parsers[ServiceOp.PROJECT])
read.make_cli(parsers[ServiceOp.READ])
session.make_cli(parsers[ServiceOp.SESSION])
tag.make_cli(parsers[ServiceOp.TAG])
tare.make_cli(parsers[ServiceOp.TARE])
user.make_cli(parsers[ServiceOp.USER])

# Execution exits on tab completion with the following line.
argcomplete.autocomplete(parser)

# Delayed import for CLI responsiveness
import logging
import sys
from .utils.privileges import drop_privileges

from growbies.constants import DEFAULT_CMD_TIMEOUT_SECONDS
from growbies.device.resp import DeviceError
from growbies.service.common import (ServiceCmd, ServiceOp, ServiceCmdError, TBaseServiceCmd)
from growbies.service.queue import IDQueue, ServiceQueue

drop_privileges()
logger = logging.getLogger(__name__)


# Execution continues here on execution not invoked by tab.
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
