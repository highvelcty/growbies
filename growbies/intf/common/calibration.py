import ctypes

from growbies.utils.report import format_float_list, format_float_table

COEFF_COUNT = 2
TARE_COUNT = 1
MASS_SENSOR_COUNT = 1
TEMPERATURE_SENSOR_COUNT = 1

class Calibration(ctypes.Structure):
    class Field:
        MASS_TEMPERATURE_COEFF = '_mass_temperature_coeff'
        MASS_COEFF = '_mass_coeff'
        TARE = '_tare'

    _pack_ = 1
    # Note: The rows must be assigned to a variable prior to use. Inlining with parenthesis does
    # not work.
    _row = ctypes.c_float * COEFF_COUNT
    _fields_ = [
        (Field.MASS_TEMPERATURE_COEFF, _row * MASS_SENSOR_COUNT),
        (Field.MASS_COEFF, ctypes.c_float * COEFF_COUNT),
        (Field.TARE, ctypes.c_float * TARE_COUNT)
    ]

    def set_sensor_data(self, field, sensor: int, *values):
        getattr(self, field)[sensor] = values

    @property
    def mass_temperature_coeff(self) -> list[list[float]]:
        ctypes_2d_array = getattr(self, self.Field.MASS_TEMPERATURE_COEFF)
        return _get_ctypes_2d_array(ctypes_2d_array)

    @mass_temperature_coeff.setter
    def mass_temperature_coeff(self, values: list[list[float]]):
        ctypes_2d_array = getattr(self, self.Field.MASS_TEMPERATURE_COEFF)
        _set_ctypes_2d_array(ctypes_2d_array, values)

    @property
    def mass_coeff(self) -> list[float]:
        return list(getattr(self, self.Field.MASS_COEFF))

    @mass_coeff.setter
    def mass_coeff(self, values: list[float]):
        for idx in range(len(getattr(self, self.Field.MASS_COEFF))):
            getattr(self, self.Field.MASS_COEFF)[idx] = values[idx]

    @property
    def tare(self) -> list[float]:
        return list(getattr(self, self.Field.TARE))

    @tare.setter
    def tare(self, values: list[float]):
        for idx in range(len(getattr(self, self.Field.TARE))):
            getattr(self, self.Field.TARE)[idx] = values[idx]

    def __str__(self):
        coeff_columns = [f'Coeff {idx}' for idx in range(COEFF_COUNT)]
        sensor_coeff_columns = ['Sensor'] + coeff_columns
        tare_columns = [f'Slot {idx}' for idx in range(TARE_COUNT)]

        str_list = [
            format_float_table('Mass/Temperature Compensation',
                               sensor_coeff_columns,
                               self.mass_temperature_coeff),
            format_float_list('Mass Calibration Coefficients', coeff_columns, self.mass_coeff),
            format_float_list('Tare', tare_columns, self.tare)
        ]

        return '\n\n'.join(str_list)


def _set_ctypes_2d_array(array, values: list[list[float]]):
    for row_idx, row in enumerate(values):
        for column_idx, value in enumerate(row):
            array[row_idx][column_idx] = value

def _get_ctypes_2d_array(array):
    return [list(array[idx]) for idx in range(len(array))]
