"""This package defines the interface to Growbies devices."""
from enum import StrEnum

from growbies.constants import APPNAME

class Op(StrEnum):
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'
    STATUS = 'status'

    @classmethod
    def get_help_str(cls, op: 'Op') -> str:
        if op == cls.STATUS:
            return f'Get {APPNAME} device status.'
        elif op == cls.CONNECT:
            return f'Stop the {APPNAME} service.'
        else:
            raise ValueError(f'Service command operation "{op}" does not exist')