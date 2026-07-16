from typing import Optional
import ctypes
import logging

from prettytable import PrettyTable

from .common import BaseStructure
from growbies.common.enum import ThermalDeviceMode, DeviceErrorCode
from growbies.common.utils.temperature import celsius_to_fahrenheit

logger = logging.getLogger(__name__)


class ThermalDeviceState(BaseStructure):
    class Field(BaseStructure.Field):
        ACTIVE = '_active'
        HEATER_ON = '_heater_on'
        FAN_ON = '_fan_on'
        MODE = '_mode'
        TEMPERATURE = '_temperature'
        DUTY_CYCLE = '_duty_cycle'
        SET_POINT = '_set_point'
        ERROR = '_error'

    _fields_ = [
        (Field.ACTIVE, ctypes.c_bool),
        (Field.HEATER_ON, ctypes.c_bool),
        (Field.FAN_ON, ctypes.c_bool),
        (Field.MODE, ctypes.c_uint8),
        (Field.TEMPERATURE, ctypes.c_float),
        (Field.DUTY_CYCLE, ctypes.c_float),
        (Field.SET_POINT, ctypes.c_float),
        (Field.ERROR, ctypes.c_float)
    ]

    @property
    def active(self) -> bool:
        return getattr(self, self.Field.ACTIVE)

    @active.setter
    def active(self, value: Optional[bool]):
        if value is not None:
            setattr(self, self.Field.ACTIVE, value)

    @property
    def heater_on(self) -> bool:
        return getattr(self, self.Field.HEATER_ON)

    @heater_on.setter
    def heater_on(self, value: bool):
        setattr(self, self.Field.HEATER_ON, value)

    @property
    def fan_on(self) -> bool:
        return getattr(self, self.Field.FAN_ON)

    @fan_on.setter
    def fan_on(self, value: bool):
        setattr(self, self.Field.FAN_ON, value)

    @property
    def mode(self) -> int:
        return getattr(self, self.Field.MODE)

    @mode.setter
    def mode(self, value: Optional[int]):
        if value is not None:
            setattr(self, self.Field.MODE, value)

    @property
    def temperature(self) -> float:
        return getattr(self, self.Field.TEMPERATURE)

    @temperature.setter
    def temperature(self, value: float):
        setattr(self, self.Field.TEMPERATURE, value)

    @property
    def duty_cycle(self) -> float:
        return getattr(self, self.Field.DUTY_CYCLE)

    @duty_cycle.setter
    def duty_cycle(self, value: Optional[float]):
        if value is not None:
            setattr(self, self.Field.DUTY_CYCLE, value)

    @property
    def set_point(self) -> float:
        return getattr(self, self.Field.SET_POINT)

    @set_point.setter
    def set_point(self, value: Optional[float]):
        if value is not None:
            setattr(self, self.Field.SET_POINT, value)

    @property
    def error(self) -> int:
        return getattr(self, self.Field.ERROR)

    @error.setter
    def error(self, value: int):
        setattr(self, self.Field.ERROR, value)

    def __str__(self):
        table = PrettyTable(title='Thermal Device State')
        table.field_names = ['Field', 'Value']

        for field in table.field_names:
            table.align[field] = 'l'

        table.add_row([
            self.Field.ACTIVE.public_name,
            self.active
        ])
        table.add_row([
            self.Field.HEATER_ON.public_name,
            self.heater_on
        ])
        table.add_row([
            self.Field.FAN_ON.public_name,
            self.fan_on
        ])
        table.add_row([
            self.Field.MODE.public_name, ThermalDeviceMode(self.mode)])
        table.add_row([
            self.Field.TEMPERATURE.public_name,
            f'{self.temperature:.2f} °C ({celsius_to_fahrenheit(self.temperature):.2f} °F)'
        ])
        table.add_row([
            self.Field.DUTY_CYCLE.public_name,
            f'{self.duty_cycle:.2f}'
        ])
        table.add_row([
            self.Field.SET_POINT.public_name,
            f'{self.set_point:.2f} °C ({celsius_to_fahrenheit(self.set_point):.2f} °F)'
        ])
        table.add_row([self.Field.ERROR.public_name, DeviceErrorCode(self.error)])

        return str(table)
