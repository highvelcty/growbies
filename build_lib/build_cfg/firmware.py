import os

from .common import Base, BASE_FILENAME, get_git_hash

from growbies.utils.paths import FirmwarePaths

PIOENV = 'PIOENV'
FILENAME = BASE_FILENAME + '.h'

class Default(Base):
    _FIRMWARE_VERSION = f'0.0.1-dev1'

    class Key(Base.Key):
        FIRMWARE_VERSION: Base.Key.type_ = 'FIRMWARE_VERSION'
        MASS_SENSOR_COUNT: Base.Key.type_ = 'MASS_SENSOR_COUNT'
        TEMPERATURE_SENSOR_COUNT: Base.Key.type_ = 'TEMPERATURE_SENSOR_COUNT'
        all = (FIRMWARE_VERSION, MASS_SENSOR_COUNT, TEMPERATURE_SENSOR_COUNT)

        @classmethod
        def value(cls, key: 'Default.Key.type_'):
            if key == cls.FIRMWARE_VERSION:
                return f'{Default._FIRMWARE_VERSION}+{get_git_hash()}'
            elif key == cls.MASS_SENSOR_COUNT:
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

class Mini(Default):
    MODEL_NUMBER = 'mini'

class Uno(Default):
    MODEL_NUMBER = 'uno'

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

class SquareEsp32c3(Default):
    MODEL_NUMBER = 'square-esp32c3'

    class Key(Default.Key):
        @classmethod
        def value(cls, key: 'Default.Key.type_'):
            if key == cls.MASS_SENSOR_COUNT:
                return 4
            elif key == cls.TEMPERATURE_SENSOR_COUNT:
                return 1
            else:
                return super().value(key)
