from pydantic import BaseModel, Field
from typing import ClassVar
from yaml import safe_load

from growbies.constants import APPNAME, YAML_INDENT
from growbies.utils.paths import InstallPaths

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
