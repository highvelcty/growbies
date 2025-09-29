from enum import StrEnum
from typing import Optional, TypeVar

class ServiceCmdError(Exception):
    pass

class ServiceOp(StrEnum):
    ACTIVATE = 'activate'
    DEACTIVATE = 'deactivate'
    CAL = 'cal'
    ID = 'id'
    LOOPBACK = 'loopback'
    LS = 'ls'
    PROJECT = 'project'
    READ = 'read'
    TAG = 'tag'
    TARE = 'tare'
    USER = 'user'

    @classmethod
    def get_help_str(cls, cmd: 'ServiceOp') -> str:
        if cmd == cls.ACTIVATE:
            return f'Activate a device.'
        elif cmd == cls.DEACTIVATE:
            return 'Deactivate a device.'
        elif cmd == cls.CAL:
            return 'Get/set device calibration.'
        elif cmd == cls.LOOPBACK:
            return 'A no operation command/response.'
        elif cmd == cls.LS:
            return f'List devices.'
        elif cmd == cls.ID:
            return f'Get/set device identify information.'
        elif cmd == cls.PROJECT:
            return f'Project management.'
        elif cmd == cls.READ:
            return f'Read a datapoint from a device.'
        elif cmd == cls.TAG:
            return f'Interface to session tagging.'
        elif cmd == cls.TARE:
            return f'Get/set mass tare.'
        elif cmd == cls.USER:
            return f'Get/set user accounts.'
        else:
            raise ValueError(f'Sub-command "{cmd}" does not exist')

    @classmethod
    def get_description_str(cls, cmd_: 'ServiceOp') -> Optional[str]:
        desc = ''
        if cmd_ == cls.ACTIVATE:
            desc = 'Making it available for connection.'
        elif cmd_ == cls.DEACTIVATE:
            desc = 'Disconnecting as necessary and making it unavailable for connection.'
        elif cmd_ == cls.CAL:
            desc = 'Read, modify or initialize device calibration.'
        elif cmd_ == cls.LOOPBACK:
            desc = 'Used to test basic command/response functionality with a device.'
        elif cmd_ == cls.LS:
            desc = 'A merge of discovered devices and devices in the DB'
        elif cmd_ == cls.ID:
            desc = f'Read, modify or initialize identify information.'
        elif cmd_ == cls.PROJECT:
            desc = f'Projects contain sessions.'
        elif cmd_ == cls.READ:
            desc = (f'A data point is a collection of measurements associated with a point in '
                    f'time.')
        elif cmd_ == cls.TARE:
            desc = f'Read, modify or initialize tare.'

        return (f'{cls.get_help_str(cmd_)}\n'
                f'\n'
                f'{desc}')

class ServiceCmd:
    def __init__(self, op: ServiceOp, kw: dict, qid: Optional[int | str] = None):
        self.op = op
        self.qid = qid
        self.kw = kw
TBaseServiceCmd = TypeVar("TBaseServiceCmd", bound=ServiceCmd)
