import ctypes
import logging

from prettytable import PrettyTable

from .common import BaseStructure
from growbies.utils.temperature import celsius_to_fahrenheit

logger = logging.getLogger(__name__)

class ThermalCfg(BaseStructure):
    class Field(BaseStructure.Field):
        ACTIVE = '_active'
        RESERVED = '_reserved'
        SET_POINT = '_set_point'

    _fields_ = [
        (Field.ACTIVE, ctypes.c_bool),
        (Field.RESERVED, ctypes.c_uint8 * 3),
        (Field.SET_POINT, ctypes.c_float),
    ]

    @property
    def active(self) -> bool:
        return getattr(self, self.Field.ACTIVE)

    @active.setter
    def active(self, value: bool):
        setattr(self, self.Field.ACTIVE, value)

    @property
    def reserved(self) -> list[int]:
        return getattr(self, self.Field.RESERVED)

    @property
    def set_point(self) -> float:
        return getattr(self, self.Field.SET_POINT)

    @set_point.setter
    def set_point(self, value: float):
        setattr(self, self.Field.SET_POINT, value)

    def __str__(self):
        table = PrettyTable(title='Thermal Device Configuration')
        table.field_names = ['Field', 'Value']

        for field in table.field_names:
            table.align[field] = 'l'

        table.add_row(['Active', self.active])
        table.add_row([
            'Set Point',
            f'{self.set_point:.2f} °C ({celsius_to_fahrenheit(self.set_point):.2f} °F)'
        ])

        return str(table)
