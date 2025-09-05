from argparse import ArgumentParser
from enum import StrEnum
from typing import ClassVar,  Optional
import logging

from pydantic import BaseModel, Field
from yaml import safe_load

from ..common import BaseServiceCmd, ServiceCmd, CMD, SUBCMD
from growbies.constants import APPNAME, YAML_INDENT
from growbies.utils.paths import InstallPaths

logger = logging.getLogger(__name__)

class Cmd(StrEnum):
    INIT = 'init'
    SHOW = 'show'

    @classmethod
    def get_help_str(cls, cmd_: 'Cmd') -> str:
        if cmd_ == cls.INIT:
            return f'Restore the user configuration to default.'
        elif cmd_ == cls.SHOW:
            return f'Output the user configuration to stdout.'
        else:
            raise ValueError(f'Database sub-command "{cmd_}" does not exist')

class InitCmdParam(StrEnum):
    YES = 'yes'

def make_cli(parser: ArgumentParser):
    parser_adder = parser.add_subparsers(dest=SUBCMD, required=False, help=f'Default: {Cmd.SHOW}')
    for cmd in Cmd:
        sub = parser_adder.add_parser(cmd, help=Cmd.get_help_str(cmd), add_help=True,
                                          argument_default=Cmd.SHOW)
        if cmd == Cmd.INIT:
            sub.add_argument(f'-{InitCmdParam.YES[0].lower()}',
                                 f'--{InitCmdParam.YES}', action='store_true', default=False)
    parser.set_defaults(**{SUBCMD: Cmd.SHOW})

class CfgCmd(BaseServiceCmd):
    sub_cmd: Cmd
    sub_cmd_kw: dict

    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.ID, **kw)

class Base(BaseModel):
    def _doc_str_to_yaml(self, _ret_str: list[str], indent: str, strip: bool = False):
        if strip:
            lines = self.__doc__.strip().splitlines()
        else:
            lines = self.__doc__.splitlines()
        for line in lines:
            _ret_str.append(f'{indent}# {line}')

    def _make_yaml(self, _ret_str: list[str], _level: int = 0):
        indent = ' ' * YAML_INDENT * _level
        # noinspection PyTypeChecker
        for key in self.model_fields:
            value = getattr(self, key)
            if isinstance(value, Base):
                _ret_str.append('')
                value._doc_str_to_yaml(_ret_str, indent, strip=True)
                _ret_str.append(f'{indent}{key}:')
                value._make_yaml(_ret_str, _level + 1)
            else:
                _ret_str.append(f'{indent}{key}: {value}')

    def __str__(self):
        ret_str = list()
        self._doc_str_to_yaml(ret_str, '')
        self._make_yaml(ret_str)
        return '\n'.join(ret_str)


class Account(Base):
    """Account configuration."""
    name: str = 'Default'

class Gateway(Base):
    """Gateway configuration."""
    name: str = 'Default'

class Cfg(Base):
    account: Account = Field(default_factory=Account)
    gateway: Gateway = Field(default_factory=Gateway)

    PATH: ClassVar = InstallPaths.ETC_GROWBIES_YAML.value

    @classmethod
    def load(cls):
        with open(cls.PATH, 'r') as inf:
            return cls(**safe_load(inf))

    def save(self):
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.PATH, 'w') as outf:
            outf.write(str(self))

Cfg.__doc__ = f'\n{APPNAME.capitalize()} configuration.\n\n'

def execute(cmd: CfgCmd) -> Optional[Cfg]:
    if cmd.cmd == Cmd.INIT:
        yes = cmd.cmd_kw.get(InitCmdParam.YES, False)
        if not yes:
            while True:
                ans = input(f'Restore {APPNAME} to default? y/n/q: ').lower().strip()
                if ans.startswith('q') or ans.startswith('n'):
                    return None
                elif ans.startswith('y'):
                    break
                else:
                    logger.error('Unrecognized input.')
        cfg = Cfg()
        cfg.save()
        print(f'Initialized {APPNAME.capitalize()} configuration at: {cfg.PATH}')
        return None
    elif cmd == Cmd.SHOW:
        return Cfg()
    else:
        return None

