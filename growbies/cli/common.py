from enum import StrEnum

_INTERNAL_FIELD_NAME_DELINEATOR = '_'

CMD = 'cmd'

class Param(StrEnum):
    FUZZY_ID = 'fuzzy_id'
    ACTION = 'action'

    @property
    def help(self) -> str:
        if self == self.FUZZY_ID:
            return ('A partial or full identifier for a database entity, such as a device, '
                    'project, session, etc.')
        elif self == self.ACTION:
            return 'The action to take.'
        else:
            return ''

def internal_to_external_field(field: str):
    return field.lstrip(_INTERNAL_FIELD_NAME_DELINEATOR)