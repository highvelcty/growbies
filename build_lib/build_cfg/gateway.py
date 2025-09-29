from typing import Any

from growbies.utils.paths import DebianPaths, RepoPaths
from .common import Base, BASE_FILENAME, get_git_hash

FILENAME = BASE_FILENAME + '.py'

class Default(Base):
    _VERSION = '0.0.1-dev0'

    class Key(Base.Key):
        VERSION: Base.Key.type_ = 'VERSION'
        all = (VERSION, )

    def save(self):
        self.validate()
        path = RepoPaths.PKG_DEB.value / DebianPaths.DEBIAN_SRC_GROWBIES.value / FILENAME
        with open(path, 'w') as outf:
            outf.write(str(self))

    def __str__(self):
        str_list = [
            '"""This file is updated by the build system at build time."""',
            ''
        ]

        for key, value in self._constants().items():
            if isinstance(value, str):
                str_list.append(f"{key} = '{value}'")
            else:
                str_list.append(f"{key} = {value}")
        str_list.append('')

        return '\n'.join(str_list)

    def _constants(self) -> dict[Base.Key.type_, Any]:
        return {
            self.Key.VERSION: f'{self._VERSION}+{get_git_hash()}'
        }
