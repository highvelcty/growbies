from enum import StrEnum
from typing import Optional, TypeVar

from pydantic import BaseModel

class Cmd(StrEnum):
    DEVICE_LS = 'device_ls'
    SERVICE_STOP = 'service_stop'


class CmdHdr(BaseModel):
    cmd: Cmd
    qid: Optional[int] = None


class BaseCmd(CmdHdr):
    pass
TBaseCmd = TypeVar('TBaseCmd', bound=BaseCmd)


class DeviceLsCmd(BaseCmd):
    def __init__(self, **kw):
        super().__init__(cmd=Cmd.DEVICE_LS, **kw)

class ServiceStopCmd(BaseCmd):
    def __init__(self):
        super().__init__(cmd=Cmd.SERVICE_STOP)
