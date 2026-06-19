from typing import cast
import os

from .common import Base, BASE_FILENAME, get_git_hash, EnvironVars

from growbies.utils.paths import FirmwarePaths

PIOENV = 'PIOENV'
FILENAME = BASE_FILENAME + '.h'

class Default(Base):
    _FIRMWARE_VERSION = f'1.0.8'

    class Key(Base.Key):
        FIRMWARE_VERSION: Base.Key.type_ = 'FIRMWARE_VERSION'
        PIN_CFG: Base.Key.type_ = 'PIN_CFG'
        MASS_SENSOR_COUNT: Base.Key.type_ = 'MASS_SENSOR_COUNT'
        MODEL_NUMBER: Base.Key.type_ = 'MODEL_NUMBER'
        TEMPERATURE_SENSOR_COUNT: Base.Key.type_ = 'TEMPERATURE_SENSOR_COUNT'
        all = (FIRMWARE_VERSION, MASS_SENSOR_COUNT, MODEL_NUMBER, PIN_CFG,
               TEMPERATURE_SENSOR_COUNT)

        @classmethod
        def value(cls, key: 'Default.Key.type_') -> str | int:
            if key == cls.FIRMWARE_VERSION:
                return f'{Default._FIRMWARE_VERSION}+{get_git_hash()}'
            elif key == cls.MASS_SENSOR_COUNT:
                return 1
            elif key == cls.MODEL_NUMBER:
                return EnvironVars.MODEL_NUMBER.value
            elif key == cls.PIN_CFG:
                return 1
            elif key == cls.TEMPERATURE_SENSOR_COUNT:
                return 1
            else:
                raise ValueError(key)

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

        for key in self.Key.all:
            value = self.Key.value(key)
            if isinstance(value, str):
                str_list.append(f'#define {key} "{value}"')
            else:
                str_list.append(f'#define {key} {value}')

        str_list.append('')
        str_list.append('')

        return '\n'.join(str_list)

class Esp32c3(Default):
    MODEL_NUMBER = 'esp32c3'

class CircleEsp32c3(Default):
    MODEL_NUMBER = 'circle-esp32c3'

    class Key(Default.Key):
        @classmethod
        def value(cls, key: 'Default.Key.type_'):
            if key == cls.MASS_SENSOR_COUNT:
                return 3
            elif key == cls.TEMPERATURE_SENSOR_COUNT:
                return 3
            else:
                return super().value(key)


# noinspection PyPep8Naming
class Circle1(CircleEsp32c3):
    MODEL_NUMBER = 'circle-1'

# noinspection PyPep8Naming
class Circle2(Circle1):
    MODEL_NUMBER = 'circle-2'

    class Key(CircleEsp32c3.Key):
        @classmethod
        def value(cls, key: 'Default.Key.type_'):
            if key == cls.PIN_CFG:
                return 2
            else:
                return super().value(key)
