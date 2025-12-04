import logging

from . import eval_, ls, mon, new, plot, resume, stop
from growbies.cli.common import SUBCMD
from growbies.cli.cal import SubCmd
from growbies.service.common import ServiceOp, ServiceCmd, ServiceCmdError

__all__ = ['execute']

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd):
    subcmd = cmd.kw.pop(SUBCMD)

    if subcmd == SubCmd.EVAL:
        return eval_.execute(cmd)
    elif subcmd == SubCmd.LS:
        return ls.execute(cmd)
    elif subcmd == SubCmd.MON:
        return mon.execute(cmd)
    elif subcmd == SubCmd.NEW:
        return new.execute(cmd)
    elif subcmd == SubCmd.PLOT:
        return plot.execute(cmd)
    elif subcmd == SubCmd.RESUME:
        return resume.execute(cmd)
    elif subcmd == SubCmd.STOP:
        return stop.execute(cmd)
    raise ServiceCmdError(f'Invalid {ServiceOp.CAL} sub-cmd "{subcmd}".')
