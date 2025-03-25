"""This package defines the gateway service."""
from enum import StrEnum

from growbies.constants import APPNAME

class Op(StrEnum):
    START = 'start'
    STOP = 'stop'

    @classmethod
    def get_help_str(cls, op: 'Op') -> str:
        if op == cls.START:
            return f'Start the {APPNAME} service.'
        elif op == cls.STOP:
            return f'Stop the {APPNAME} service.'
        else:
            raise ValueError(f'Service command operation "{op}" does not exist')