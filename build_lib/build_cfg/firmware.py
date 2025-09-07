import os
from typing import Any

from .common import Base, BASE_FILENAME, get_git_hash

from growbies.utils.paths import FirmwarePaths

PIOENV = 'PIOENV'
FILENAME = BASE_FILENAME + '.h'

class Default(Base):
    _FIRMWARE_VERSION = f'0.0.1-dev0'

    class Key(Base.Key):
        FIRMWARE_VERSION: Base.Key.type_ = 'FIRMWARE_VERSION'
        all = (FIRMWARE_VERSION, )

    def save(self):
        self.validate()
        path = FirmwarePaths.FIRMWARE_PIO_BUILD.value / os.environ[PIOENV] / FILENAME
        with open(path, 'w') as outf:
            outf.write(str(self))

    def __str__(self):
        str_list = [
            '// This file created by the build system at build time.',
            '',
            '#pragma once',
            ''
        ]

        for key, value in self._constants().items():
            if isinstance(value, str):
                str_list.append(f'#define {key} "{value}"')
            else:
                str_list.append(f'#define {key} {value}')

        str_list.append('')
        str_list.append('')

        return '\n'.join(str_list)

    def _constants(self) -> dict[Base.Key.type_, Any]:
        return {
            self.Key.FIRMWARE_VERSION: f'{self._FIRMWARE_VERSION}+{get_git_hash()}'
        }
