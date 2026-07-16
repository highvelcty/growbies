import logging

from . import calibration, identify, tare
from growbies.cli.common import SUBCMD
from growbies.cli.nvm import SubCmd
from growbies.protocol.common.calibration import Calibration
from growbies.protocol.common.identify import TNvmIdentify
from growbies.protocol.common.tare import Tares
from growbies.service.common import ServiceOp, ServiceCmd, ServiceCmdError

__all__ = ['execute']

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> Calibration | Tares | TNvmIdentify | None:
    subcmd = cmd.kw.pop(SUBCMD)

    if subcmd == SubCmd.CAL:
        return calibration.execute(cmd)
    elif subcmd == SubCmd.ID:
        return identify.execute(cmd)
    elif subcmd == SubCmd.TARE:
        return tare.execute(cmd)
    raise ServiceCmdError(f'Invalid {ServiceOp.NVM} sub-cmd "{subcmd}".')
