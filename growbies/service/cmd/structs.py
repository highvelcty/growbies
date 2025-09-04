from enum import StrEnum
from typing import Optional, TypeVar

from pydantic import BaseModel, Field

from growbies.utils.types import Serial_t

__all__ = ['BaseServiceCmd', 'ServiceCmd', 'TBaseServiceCmd',
           'ActivateServiceCmd', 'DeactivateServiceCmd', 'IdServiceCmd', 'LsServiceCmd',
           'LoopbackServiceCmd']

class ServiceCmd(StrEnum):
    ACTIVATE = 'activate'
    DEACTIVATE = 'deactivate'
    ID = 'id'
    LOOPBACK = 'loopback'
    LS = 'ls'

    @classmethod
    def get_help_str(cls, cmd_: 'ServiceCmd') -> str:
        if cmd_ == cls.ACTIVATE:
            return f'Activate a device.'
        elif cmd_ == cls.DEACTIVATE:
            return ('Deactivate a device. Disconnecting as necessary and making it unavailable '
                    'for connection.')
        elif cmd_ == cls.LOOPBACK:
            return 'A no operation command/response.'
        elif cmd_ == cls.LS:
            return f'List devices.'
        elif cmd_ == cls.ID:
            return f'Identify a device.'
        else:
            raise ValueError(f'Sub-command "{cmd_}" does not exist')

    @classmethod
    def get_description_str(cls, cmd_: 'ServiceCmd') -> Optional[str]:
        desc = ''
        if cmd_ == cls.ACTIVATE:
            desc = 'Making it available for connection.'
        elif cmd_ == cls.DEACTIVATE:
            desc = 'Disconnecting as necessary and making it unavailable for connection.'
        elif cmd_ == cls.LOOPBACK:
            desc = 'Used to test basic command/response functionality with a device.'
        elif cmd_ == cls.LS:
            desc = 'A merge of discovered devices and devices in the DB'
        elif cmd_ == cls.ID:
            desc = (f'If any keyword parameter is given, a read/mod/write/verify will occur. '
                    f'Otherwise, only a read will occur.')

        return (f'{cls.get_help_str(cmd_)}\n'
                f'\n'
                f'{desc}')

class BaseServiceCmd(BaseModel):
    cmd: ServiceCmd
    qid: Optional[int|str] = None
TBaseServiceCmd = TypeVar('TBaseServiceCmd', bound=BaseServiceCmd)

class IdServiceCmd(BaseServiceCmd):
    serial: Serial_t
    device_cmd_kw: dict
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.ID, **kw)

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
