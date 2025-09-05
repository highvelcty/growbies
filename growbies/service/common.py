from enum import StrEnum
from typing import Optional, TypeVar

from pydantic import BaseModel

from growbies.utils.paths import InstallPaths

class ServiceCmdError(Exception):
    pass

CMD = 'cmd'
SUBCMD = 'subcmd'

class PositionalParam(StrEnum):
    SERIAL = 'serial'
    SERIALS = 'serials'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'PositionalParam') -> str:
        if sub_cmd_ == cls.SERIAL:
            return 'The serial number of a device.'
        elif sub_cmd_ == cls.SERIALS:
            return 'A list of serial numbers. This can be unique partial matches.'
        raise ValueError(f'"{sub_cmd_} does not exist.')

class ServiceCmd(StrEnum):
    ACTIVATE = 'activate'
    DEACTIVATE = 'deactivate'
    CFG = 'cfg'
    ID = 'id'
    LOOPBACK = 'loopback'
    LS = 'ls'

    @classmethod
    def get_help_str(cls, cmd_: 'ServiceCmd') -> str:
        if cmd_ == cls.ACTIVATE:
            return f'Activate a device.'
        elif cmd_ == cls.DEACTIVATE:
            return 'Deactivate a device.'
        elif cmd_ == cls.CFG:
            return 'User configuration file interface.'
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
        elif cmd_ == cls.CFG:
            desc = f'Located at {InstallPaths.ETC_GROWBIES_YAML.value}'
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
