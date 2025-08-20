from enum import StrEnum
from typing import Optional, TypeVar

from pydantic import BaseModel, Field

from growbies.utils.types import Serial_t

__all__ = ['Cmd', 'BaseCmd', 'DeviceLsCmd', 'ActivateCmd', 'DeactivateCmd',
           'ServiceStopCmd', 'TBaseCmd']

class Cmd(StrEnum):
    LS = 'ls'
    ACTIVATE = 'activate'
    DEACTIVATE = 'deactivate'
    RECONNECT = 'reconnect'
    SERVICE_STOP = 'service_stop'


class BaseCmd(BaseModel):
    cmd: Cmd
    qid: Optional[int|str] = None
TBaseCmd = TypeVar('TBaseCmd', bound=BaseCmd)


class DeviceLsCmd(BaseCmd):
    def __init__(self, **kw):
        super().__init__(cmd=Cmd.LS, **kw)

class ActivateCmd(BaseCmd):
    serials: list[Serial_t] = Field(default_factory=list, min_length=1)
    def __init__(self, **kw):
        super().__init__(cmd=Cmd.ACTIVATE, **kw)

class DeactivateCmd(BaseCmd):
    serials: list[Serial_t] = Field(default_factory=list, min_length=1)
    def __init__(self, **kw):
        super().__init__(cmd=Cmd.DEACTIVATE, **kw)

class ReconnectCmd(BaseCmd):
    serials: list[Serial_t] = Field(default_factory=list, min_length=1)
    def __init__(self, **kw):
        super().__init__(cmd=Cmd.RECONNECT, **kw)

class ServiceStopCmd(BaseCmd):
    def __init__(self):
        super().__init__(cmd=Cmd.SERVICE_STOP)
