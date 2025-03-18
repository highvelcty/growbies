"""This package defines the background gateway service."""
from enum import StrEnum

from growbies.constants import APPNAME

class Cmd(StrEnum):
    START = 'start'
    STOP = 'stop'

    @classmethod
    def get_help_str(cls, param: 'Cmd') -> str:
        if param == cls.START:
            return f'Start the {APPNAME} service.'
        elif param == cls.STOP:
            return f'Stop the {APPNAME} service.'
        else:
            raise ValueError(f'Service command "{param}" does not exist')