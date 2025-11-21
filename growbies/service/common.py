from enum import StrEnum
from typing import Optional, TypeVar

class ServiceCmdError(Exception):
    pass

class ServiceOp(StrEnum):
    CAL = 'cal'
    DEVICE = 'device'
    ID = 'id'
    PROJECT = 'project'
    READ = 'read'
    SESSION = 'session'
    TAG = 'tag'
    TARE = 'tare'
    USER = 'user'

    @property
    def help(self) -> str:
        if self == self.DEVICE:
            return 'Physical device interface and management.'
        elif self == self.ID:
            return f'Get/set device identify information.'
        elif self == self.PROJECT:
            return f'Project management.'
        elif self == self.READ:
            return f'Read a datapoint from a device.'
        elif self == self.SESSION:
            return f'Session management.'
        elif self == self.TAG:
            return f'Interface to session tagging.'
        elif self == self.TARE:
            return f'Get/set mass tare.'
        elif self == self.USER:
            return f'Get/set user accounts.'
        else:
            return ''

    @property
    def description(self) -> str:
        desc = ''
        if self == self.CAL:
            desc = f'List/modify/initialize device calibration.'
        elif self == self.ID:
            desc = f'List/modify/initialize device identify information.'
        elif self == self.PROJECT:
            desc = f'Projects contain sessions.'
        elif self == self.READ:
            desc = (f'A data point is a collection of measurements associated with a point in '
                    f'time.')
        elif self == self.SESSION:
            desc = f'List/add/modify/remove sessions.'
        elif self == self.TAG:
            desc = f'List/add/modify/remove tags.'
        elif self == self.TARE:
            desc = f'Read, modify or initialize tare.'
        elif self == self.USER:
            desc = f'List/add/modify/remove users.'

        return (f'{self.help}\n'
                f'\n'
                f'{desc}')

class ServiceCmd:
    def __init__(self, op: ServiceOp, kw: dict, qid: Optional[int | str] = None):
        self.op = op
        self.qid = qid
        self.kw = kw
TBaseServiceCmd = TypeVar("TBaseServiceCmd", bound=ServiceCmd)
