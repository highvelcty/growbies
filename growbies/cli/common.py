from enum import StrEnum

_INTERNAL_FIELD_NAME_DELINEATOR = '_'

CMD = 'cmd'

class PositionalParam(StrEnum):
    FUZZY_ID = 'fuzzy_id'
    SERIAL = 'serial'
    SERIALS = 'serials'

    @property
    def help(self) -> str:
        if self == self.FUZZY_ID:
            return 'A partial ID or name of device.'
        elif self == self.SERIAL:
            return 'The serial number of a device.'
        elif self == self.SERIALS:
            return 'A list of serial numbers. This can be unique partial matches.'
        raise ValueError(f'"{self} does not exist.')

    @classmethod
    def get_help_str(cls, sub_cmd_: 'PositionalParam') -> str:
        if sub_cmd_ == cls.SERIAL:
            return 'The serial number of a device.'
        elif sub_cmd_ == cls.SERIALS:
            return 'A list of serial numbers. This can be unique partial matches.'
        raise ValueError(f'"{sub_cmd_} does not exist.')


class Param(StrEnum):
    FUZZY_ID = 'fuzzy_id'
    ACTION = 'action'

    @property
    def help(self) -> str:
        if self == self.FUZZY_ID:
            return 'The session to operate on.'
        elif self == self.ACTION:
            return 'The action to take.'
        else:
            return ''

def internal_to_external_field(field: str):
    return field.lstrip(_INTERNAL_FIELD_NAME_DELINEATOR)