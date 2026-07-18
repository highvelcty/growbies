from enum import IntEnum

class DynamicIntEnum(IntEnum):
    """Dynamically add elements if attempting to create from an unimplemented value."""
    @classmethod
    def _missing_(cls, value):
        obj = int.__new__(cls, value)
        obj._name_ = f'UNKNOWN_{value}'
        obj._value_ = value
        return obj

    def __str__(self):
        return f'{self.value}: {self.name}'


class DeviceErrorCode(DynamicIntEnum):
    # bitfield
    NONE                                  = 0
    CMD_DESERIALIZATION_BUFFER_UNDERFLOW  = 1
    UNRECOGNIZED_COMMAND                  = 2
    INCOMPLETE_SLIP_FRAME                 = 3
    INVALID_SLIP_CRC                      = 4
    CMD_HDR_DESERIALIZATION_UNDERFLOW     = 5
    ERROR_HEATER_STATE_TRANSITION_TIMEOUT = 6,

class ThermalDeviceErrorCode(DynamicIntEnum):
    NONE = 0
    ERROR_HEATER_STATE_TRANSITION_TIMEOUT = 1
    ERROR_TEMPERATURE_TOO_HIGH = 2

class ThermalDeviceMode(DynamicIntEnum):
    AUTO = 0
    MANUAL = 1
