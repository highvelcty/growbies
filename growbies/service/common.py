from enum import StrEnum
from typing import Optional, TypeVar

class ServiceCmdError(Exception):
    pass

class ServiceOp(StrEnum):
    CAL = 'cal'
    DEVICE = 'device'
    NVM = 'nvm'
    PROJECT = 'project'
    READ = 'read'
    SESSION = 'session'
    TAG = 'tag'
    USER = 'user'

    @property
    def help(self) -> str:
        if self == self.CAL:
            return 'Device Calibration application interface.'
        elif self == self.DEVICE:
            return 'Physical device interface and management.'
        elif self == self.NVM:
            return f'Access Non-volatile memory backed data.'
        elif self == self.PROJECT:
            return f'Project management.'
        elif self == self.READ:
            return f'Read a datapoint from a device.'
        elif self == self.SESSION:
            return f'Session management.'
        elif self == self.TAG:
            return f'Interface to session tagging.'
        elif self == self.USER:
            return f'Get/set user accounts.'
        else:
            return ''

    @property
    def description(self) -> str:
        desc = ''
        if self == self.CAL:
            desc = 'A utility application to aid in device calibration.'
        elif self == self.DEVICE:
            desc = f'Physical device interface and management.'
        elif self == self.NVM:
            desc = f'List/modify/initialize non-volatile memory data.'
        elif self == self.PROJECT:
            desc = f'Projects contain sessions.'
        elif self == self.READ:
            desc = (f'A data point is a collection of measurements associated with a point in '
                    f'time.')
        elif self == self.SESSION:
            desc = f'List/add/modify/remove sessions.'
        elif self == self.TAG:
            desc = f'List/add/modify/remove tags.'
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
