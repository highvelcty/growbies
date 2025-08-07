from pydantic import BaseModel, Field
from typing import ClassVar
from yaml import safe_load_all

from growbies.constants import APPNAME, YAML_INDENT
from growbies.utils.paths import InstallPaths


class BaseCfg(BaseModel):
    def _format_doc_str(self, _ret_str: list[str], indent: str, strip: bool = False):
        if strip:
            lines = self.__doc__.strip().splitlines()
        else:
            lines = self.__doc__.splitlines()
        for line in lines:
            _ret_str.append(f'{indent}# {line}')

    def _recursive_str(self, _ret_str: list[str], _level: int = 0):
        indent = ' ' * YAML_INDENT * _level
        # noinspection PyTypeChecker
        for key in self.model_fields:
            value = getattr(self, key)
            if isinstance(value, BaseCfg):
                _ret_str.append('')
                value._format_doc_str(_ret_str, indent, strip=True)
                _ret_str.append(f'{indent}{key}:')
                value._recursive_str(_ret_str, _level + 1)
            else:
                _ret_str.append(f'{indent}{key}: {value}')

class Account(BaseCfg):
    """Account configuration."""
    name: str = 'Default'

class Gateway(BaseCfg):
    """Gateway configuration."""
    name: str = 'Default'

class Cfg(BaseCfg):
    account: Account = Field(default_factory=Account)
    gateway: Gateway = Field(default_factory=Gateway)

    PATH: ClassVar = InstallPaths.ETC_GROWBIES_YAML.value

    @classmethod
    def load(cls):
        return cls(**next(safe_load_all(cls.PATH)))

    def save(self):
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.PATH, 'w') as outf:
            outf.write(str(self))

    def __str__(self):
        ret_str = list()
        self._format_doc_str(ret_str, '')
        self._recursive_str(ret_str)
        return '\n'.join(ret_str)

Cfg.__doc__ = f'\n{APPNAME.capitalize()} configuration.\n\n'
