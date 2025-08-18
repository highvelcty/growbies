from enum import StrEnum
from typing import Optional, TypeVar

from pydantic import BaseModel, Field

from growbies.utils.types import Serial_t

__all__ = ['Cmd', 'BaseCmd', 'DeviceLsCmd', 'ActivateCmd', 'DeactivateCmd',
           'ServiceStopCmd', 'TBaseCmd']

class Cmd(StrEnum):
    DEVICE_LS = 'device_ls'
    DEVICE_ACTIVATE = 'device_activate'
    DEVICE_DEACTIVATE = 'device_deactivate'
    SERVICE_STOP = 'service_stop'


class BaseCmd(BaseModel):
    cmd: Cmd
    qid: Optional[int] = None
TBaseCmd = TypeVar('TBaseCmd', bound=BaseCmd)


class DeviceLsCmd(BaseCmd):
    def __init__(self, **kw):
        super().__init__(cmd=Cmd.DEVICE_LS, **kw)

class ActivateCmd(BaseCmd):
    serials: list[Serial_t] = Field(default_factory=list, min_length=1)
    def __init__(self, **kw):
        super().__init__(cmd=Cmd.DEVICE_ACTIVATE, **kw)

class DeactivateCmd(BaseCmd):
    serials: list[Serial_t] = Field(default_factory=list, min_length=1)
    def __init__(self, **kw):
        super().__init__(cmd=Cmd.DEVICE_DEACTIVATE, **kw)

class ServiceStopCmd(BaseCmd):
    def __init__(self):
        super().__init__(cmd=Cmd.SERVICE_STOP)
