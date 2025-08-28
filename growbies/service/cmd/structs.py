from typing import Literal, NewType, Optional, TypeVar

from pydantic import BaseModel, Field

from growbies.utils.types import Serial_t

__all__ = ['BaseServiceCmd', 'ServiceCmd', 'TBaseServiceCmd',
           'ActivateServiceCmd', 'DeactivateServiceCmd', 'LsServiceCmd', 'LoopbackServiceCmd',
           'ServiceStopServiceCmd']

class ServiceCmd:
    # noinspection PyNewType
    type_ = NewType('ServiceCmd', str)
    ACTIVATE = type_("activate")
    DEACTIVATE = type_("deactivate")
    LOOPBACK = type_("loopback")
    LS = type_("ls")
    SERVICE_STOP = type_("service_stop")

    external_cmds = (ACTIVATE, DEACTIVATE, LOOPBACK, LS)

    @classmethod
    def get_help_str(cls, cmd_: 'ServiceCmd.type_') -> str:
        if cmd_ == cls.ACTIVATE:
            return f'Activate a device, making it available for connection.'
        elif cmd_ == cls.DEACTIVATE:
            return ('Deactivate a device. Disconnecting as necessary and making it unavailable '
                    'for connection.')
        elif cmd_ == cls.LOOPBACK:
            return 'The loopback command will test round trip command/response functionality.'
        elif cmd_ == cls.LS:
            return f'List discovered devices merged with known devices in the DB.'
        elif cmd_ == cls.SERVICE_STOP:
            return 'Stop the service.'
        else:
            raise ValueError(f'Sub-command "{cmd_}" does not exist')


class BaseServiceCmd(BaseModel):
    cmd: ServiceCmd.type_
    qid: Optional[int|str] = None
TBaseServiceCmd = TypeVar('TBaseServiceCmd', bound=BaseServiceCmd)


class LsServiceCmd(BaseServiceCmd):
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.LS, **kw)

class ActivateServiceCmd(BaseServiceCmd):
    serials: list[Serial_t] = Field(default_factory=list, min_length=1)
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.ACTIVATE, **kw)

class DeactivateServiceCmd(BaseServiceCmd):
    serials: list[Serial_t] = Field(default_factory=list, min_length=1)
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.DEACTIVATE, **kw)

class LoopbackServiceCmd(BaseServiceCmd):
    serial: Serial_t
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.LOOPBACK, **kw)

class ServiceStopServiceCmd(BaseServiceCmd):
    def __init__(self):
        super().__init__(cmd=ServiceCmd.SERVICE_STOP)
