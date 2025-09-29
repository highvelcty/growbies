from enum import StrEnum

_INTERNAL_FIELD_NAME_DELINEATOR = '_'

CMD = 'cmd'

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


def internal_to_external_field(field: str):
    return field.lstrip(_INTERNAL_FIELD_NAME_DELINEATOR)