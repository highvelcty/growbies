from utils.paths import RepoPaths
from .common import Base, BASE_FILENAME

FILENAME = BASE_FILENAME + '.py'

class BaseFw(Base):
    class Key(Base.Key):
        MASS_SENSOR_COUNT = 1
        TEMPERATURE_SENSOR_COUNT = 1

    _constants = Base._constants

    _path = RepoPaths.GROWBIES.value / FILENAME

    def save(self):
        with open(self._path, 'w') as outf:
            outf.write(str(self))

    def __str__(self):
        str_list = list()

        for key, value in self._constants().items():
            str_list.append(f'{key} = {value}')

        return '\n'.join(str_list)

class Default(BaseFw):
    MODEL_NUMBER = 'default'
