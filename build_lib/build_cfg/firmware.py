import os
from typing import Any

from .common import Base, BASE_FILENAME, get_git_hash

from growbies.utils.paths import FirmwarePaths

PIOENV = 'PIOENV'
FILENAME = BASE_FILENAME + '.h'

class BaseFw(Base):
    class Key(Base.Key):
        MASS_SENSOR_COUNT: Base.Key.type_ = 'MASS_SENSOR_COUNT'
        TEMPERATURE_SENSOR_COUNT: Base.Key.type_ = 'TEMPERATURE_SENSOR_COUNT'

        all = Base.Key.all + (MASS_SENSOR_COUNT, TEMPERATURE_SENSOR_COUNT)

    def _constants(self) -> dict[Base.Key.type_, Any]:
        ret_dict = super()._constants()
        ret_dict[self.Key.VERSION] = f'0.0.1-dev0+{get_git_hash()}'
        ret_dict[self.Key.MASS_SENSOR_COUNT] = 1
        ret_dict[self.Key.TEMPERATURE_SENSOR_COUNT] = 1
        return ret_dict

    def save(self):
        path = FirmwarePaths.FIRMWARE_PIO_BUILD.value / os.environ[PIOENV] / FILENAME
        with open(path, 'w') as outf:
            outf.write(str(self))

    def __str__(self):
        str_list = [
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

class Default(BaseFw):
    MODEL_NUMBER = 'MICRO_ESP32C3-MASS_1-TEMP_1-COMM_USB-0'

    def _constants(self) -> dict[Base.Key.type_, Any]:
        ret_dict = super()._constants()
        ret_dict[self.Key.MODEL_NUMBER] = self.MODEL_NUMBER
        return ret_dict
