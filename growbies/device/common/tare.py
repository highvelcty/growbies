import ctypes

from . import nvm
from .common import BaseStructure, MassUnitsType
from growbies.utils.report import PRECISION
from growbies.utils.timestamp import get_elapsed_str

class Tare(BaseStructure):
    class Field(BaseStructure.Field):
        VALUE = '_value'
        DISPLAY_UNITS = '_display_units'
        RESERVED = '_reserved'
        TIMESTAMP = '_timestamp'

    _fields_ = [
        (Field.VALUE, ctypes.c_float),
        (Field.DISPLAY_UNITS, ctypes.c_uint8),
        (Field.RESERVED, ctypes.c_uint8 * 3),
        (Field.TIMESTAMP, ctypes.c_uint32)
    ]

    @property
    def value(self) -> float:
        return getattr(self, self.Field.VALUE)

    @value.setter
    def value(self, value: float):
        setattr(self, self.Field.VALUE, value)

    @property
    def display_units(self) -> MassUnitsType:
        return MassUnitsType(getattr(self, self.Field.DISPLAY_UNITS))

    @display_units.setter
    def display_units(self, value: MassUnitsType):
        setattr(self, self.Field.DISPLAY_UNITS, value)

    @property
    def reserved(self) -> list[int]:
        return getattr(self, self.Field.RESERVED)

    @property
    def timestamp(self) -> int:
        return getattr(self, self.Field.TIMESTAMP)

    @timestamp.setter
    def timestamp(self, value: int):
        setattr(self, self.Field.TIMESTAMP, value)

class Tares(BaseStructure):
    TARE_COUNT = 8
    USER_SLOTS = (0,1,2)
    GLOBAL_SLOT = TARE_COUNT - 1
    class Field(BaseStructure.Field):
        TARES = '_tares'

    _fields_ = [
        (Field.TARES, Tare * TARE_COUNT)
    ]

    @classmethod
    def get_name(cls, slot: int) -> str:
        if slot in cls.USER_SLOTS:
            return f'Tare {slot}'
        elif slot == cls.GLOBAL_SLOT:
            return 'Global'
        elif slot < cls.GLOBAL_SLOT:
            return f'Reserved {slot}'
        else:
            raise IndexError(f'Slot {slot} is out of range [0, {cls.TARE_COUNT - 1}].')

    @classmethod
    def get_description(cls, slot: int) -> str:
        if slot in cls.USER_SLOTS:
            return 'General purpose user tare slot.'
        elif slot == cls.GLOBAL_SLOT:
            return ('Global tare value that is subtracted from the measured mass prior to '
                    'subtracting all other tare slots.')
        elif slot < cls.GLOBAL_SLOT:
            return f'Reserved'
        else:
            raise IndexError(f'Slot {slot} is out of range [0, {cls.TARE_COUNT - 1}].')

    @property
    def tares(self) -> list[Tare]:
        return getattr(self, self.Field.TARES)

    def __str__(self):
        lines = list()
        lines.append("Tares:")

        for slot, tare in enumerate(self.tares):
            lines.append(f'  slot: {slot}')
            lines.append(f'    name: {self.get_name(slot)}')
            lines.append(f'    description: {self.get_description(slot)}')
            lines.append(f'    value: {round(tare.value, PRECISION)}')
            lines.append(f'    display_units: {str(tare.display_units).lower()}')
            lines.append(f'    timestamp: {get_elapsed_str(tare.timestamp)}')

        return "\n".join(lines)


class NvmTare(nvm.BaseNvm):
    _fields_ = [
        (nvm.BaseNvm.Field.HDR, nvm.NvmHdr),
        (nvm.BaseNvm.Field.PAYLOAD, Tares)
    ]

    @property
    def payload(self) -> Tares:
        return super().payload

    @payload.setter
    def payload(self, value: Tares):
        super().payload = value
