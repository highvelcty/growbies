from growbies.utils import paths

print(paths.DebianPaths.DEBIAN_SRC_GROWBIES)

class Base:
    class Key:
        MASS_SENSOR_COUNT = 'MASS_SENSOR_COUNT'
        TEMPERATURE_SENSOR_COUNT = 'TEMPERATURE_SENSOR_COUNT'

    settings = {
        Key.MASS_SENSOR_COUNT: 1,
        Key.TEMPERATURE_SENSOR_COUNT: 1
    }


class BaseFw(Base):

    def __str__(self):
        ret_str = list()

        for key, value in self.settings:
            ret_str.append(f'#define key value')

class