from typing import Any

from growbies.utils.paths import DebianPaths, RepoPaths
from .common import Base, BASE_FILENAME, get_git_hash

FILENAME = BASE_FILENAME + '.py'

class BaseGateway(Base):
    class Key(Base.Key):
        MASS_SENSOR_COUNT = 1
        TEMPERATURE_SENSOR_COUNT = 1

    def save(self):
        path = RepoPaths.PKG_DEB.value / DebianPaths.DEBIAN_SRC_GROWBIES.value / FILENAME
        with open(path, 'w') as outf:
            outf.write(str(self))

    def _constants(self) -> dict[Key.type_, Any]:
        ret_dict = super()._constants()
        ret_dict[self.Key.VERSION] = f'0.0.1-dev0+{get_git_hash()}'
        return ret_dict

    def __str__(self):
        str_list = list()

        for key, value in self._constants().items():
            if isinstance(value, str):
                str_list.append(f"{key} = '{value}'")
            else:
                str_list.append(f"{key} = {value}")
        str_list.append('')

        return '\n'.join(str_list)

class Default(BaseGateway):
    MODEL_NUMBER = 'default'
