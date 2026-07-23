from typing import Optional
import ctypes
import logging

from prettytable import PrettyTable

from .common import BaseStructure
from growbies.common.enum import ThermalDeviceMode, ThermalDeviceErrorCode
from growbies.common.utils.temperature import celsius_to_fahrenheit

logger = logging.getLogger(__name__)

class ThermalDeviceControl(BaseStructure):
    class Field(BaseStructure.Field):
        ACTIVE = '_active'
        MODE = '_mode'
        RESERVED = '_reserved'
        DUTY_CYCLE = '_duty_cycle'
        SET_POINT = '_set_point'

    _fields_ = [
        (Field.ACTIVE, ctypes.c_bool),
        (Field.MODE, ctypes.c_uint8),
        (Field.RESERVED, ctypes.c_uint8 * 2),
        (Field.DUTY_CYCLE, ctypes.c_float),
        (Field.SET_POINT, ctypes.c_float),
    ]

    @property
    def active(self) -> bool:
        return getattr(self, self.Field.ACTIVE)

    @active.setter
    def active(self, value: Optional[bool]):
        setattr(self, self.Field.ACTIVE, value)

    @property
    def mode(self) -> int:
        return getattr(self, self.Field.MODE)

    @mode.setter
    def mode(self, value: Optional[int]):
        setattr(self, self.Field.MODE, value)

    @property
    def reserved(self) -> list[int]:
        return getattr(self, self.Field.RESERVED)

    @property
    def duty_cycle(self) -> float:
        return getattr(self, self.Field.DUTY_CYCLE)

    @duty_cycle.setter
    def duty_cycle(self, value: Optional[float]):
        setattr(self, self.Field.DUTY_CYCLE, value)

    @property
    def set_point(self) -> float:
        return getattr(self, self.Field.SET_POINT)

    @set_point.setter
    def set_point(self, value: Optional[float]):
        setattr(self, self.Field.SET_POINT, value)

    def __str__(self):
        table = PrettyTable(title="Thermal Device Control")
        table.field_names = ["Field", "Value"]

        for field in table.field_names:
            table.align[field] = "l"

        table.add_row([
            self.Field.ACTIVE.public_name,
            self.active
        ])

        table.add_row([
            self.Field.MODE.public_name,
            ThermalDeviceMode(self.mode)
        ])

        table.add_row([
            self.Field.DUTY_CYCLE.public_name,
            f"{self.duty_cycle:.1f} %"
        ])

        table.add_row([
            self.Field.SET_POINT.public_name,
            f"{self.set_point:.2f} °C "
            f"({celsius_to_fahrenheit(self.set_point):.2f} °F)"
        ])

        return str(table)

class ThermalDeviceSense(BaseStructure):
    class Field(BaseStructure.Field):
        HEATER_ON = '_heater_on'
        FAN_ON = '_fan_on'
        RESERVED = '_reserved'
        ERROR = '_error'
        TEMPERATURE = '_temperature'
        DUTY_CYCLE = '_duty_cycle'
        SET_POINT = '_set_point'
        PROPORTIONAL_DUTY_CYCLE = '_proportional_duty_cycle'
        INTEGRAL_DUTY_CYCLE = '_integral_duty_cycle'

    _fields_ = [
        (Field.HEATER_ON, ctypes.c_bool),
        (Field.RESERVED, ctypes.c_uint8 * 2),
        (Field.FAN_ON, ctypes.c_bool),
        (Field.ERROR, ctypes.c_uint32),
        (Field.TEMPERATURE, ctypes.c_float),
        (Field.PROPORTIONAL_DUTY_CYCLE, ctypes.c_float),
        (Field.INTEGRAL_DUTY_CYCLE, ctypes.c_float)
    ]

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
    def reserved(self) -> list[int]:
        return getattr(self, self.Field.RESERVED)

    @property
    def error(self) -> int:
        return getattr(self, self.Field.ERROR)

    @error.setter
    def error(self, value: int):
        setattr(self, self.Field.ERROR, value)

    @property
    def temperature(self) -> float:
        return getattr(self, self.Field.TEMPERATURE)

    @temperature.setter
    def temperature(self, value: float):
        setattr(self, self.Field.TEMPERATURE, value)

    @property
    def proportional_duty_cycle(self) -> float:
        return getattr(self, self.Field.PROPORTIONAL_DUTY_CYCLE)

    @property
    def integral_duty_cycle(self) -> float:
        return getattr(self, self.Field.INTEGRAL_DUTY_CYCLE)

    def __str__(self):
        table = PrettyTable(title="Thermal Device Sense")
        table.field_names = ["Field", "Value"]

        for field in table.field_names:
            table.align[field] = "l"

        table.add_row([
            self.Field.HEATER_ON.public_name,
            self.heater_on
        ])

        table.add_row([
            self.Field.FAN_ON.public_name,
            self.fan_on
        ])

        table.add_row([
            self.Field.TEMPERATURE.public_name,
            f"{self.temperature:.2f} °C "
            f"({celsius_to_fahrenheit(self.temperature):.2f} °F)"
        ])

        table.add_row([
            self.Field.PROPORTIONAL_DUTY_CYCLE.public_name,
            f"{self.proportional_duty_cycle:.2f} %"
        ])

        table.add_row([
            self.Field.INTEGRAL_DUTY_CYCLE.public_name,
            f"{self.integral_duty_cycle:.2f} %"
        ])

        table.add_row([
            self.Field.ERROR.public_name,
            ThermalDeviceErrorCode(self.error)
        ])

        return str(table)

class ThermalDeviceState(BaseStructure):
    class Field(BaseStructure.Field):
        SENSE = '_sense'
        CONTROL = '_control'

    _fields_ = [
        (Field.SENSE, ThermalDeviceSense),
        (Field.CONTROL, ThermalDeviceControl),
    ]

    @property
    def sense(self) -> ThermalDeviceSense:
        return getattr(self, self.Field.SENSE)

    @sense.setter
    def sense(self, value: ThermalDeviceSense):
        setattr(self, self.Field.SENSE, value)

    @property
    def control(self) -> ThermalDeviceControl:
        return getattr(self, self.Field.CONTROL)

    @control.setter
    def control(self, value: ThermalDeviceControl):
        setattr(self, self.Field.CONTROL, value)

    def __str__(self):
        return "\n\n".join((
            str(self.control),
            str(self.sense),
        ))
