from enum import StrEnum

CMD = 'cmd'
SUBCMD = 'subcmd'

class BaseParam(StrEnum):
    @property
    def kw_cli_name(self):
        return self.value.replace('_', '-')

class Param(BaseParam):
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
