from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, TypeVar, NewType

from growbies.utils.types import ModelNumber_t

BASE_FILENAME = 'build_cfg'
CMD = 'cmd'

class Cmd(StrEnum):
    FIRMWARE = 'firmware'
    GATEWAY = 'gateway'

    @classmethod
    def get_help_str(cls, sub_cmd_: 'Cmd') -> str:
        if sub_cmd_ == cls.FIRMWARE:
            return f'Generate the firmware build configuration.'
        elif sub_cmd_ == cls.GATEWAY:
            return f'Generate the gateway build configuration.'
        else:
            raise ValueError(f'Sub-command "{sub_cmd_}" does not exist')

class Param(StrEnum):
    MODEL_NUMBER = 'model_number`'

    @classmethod
    def get_help_str(cls, param_: 'Param'):
        if param_ == cls.MODEL_NUMBER:
            return f'The model number for which to generate the build configuration.'
        else:
            raise ValueError(f'Invalid parameter: "{param_}"')

class Base(ABC):
    class Key:
        # noinspection PyNewType
        type_ = NewType('Key', str)
        MODEL_NUMBER: type_ = 'MODEL_NUMBER'
        VERSION: type_ = 'VERSION'

        all = (MODEL_NUMBER, VERSION)

    def _constants(self) -> dict[Key.type_, Any]:
        return {
            self.Key.VERSION: '1.2.3-dev0+12345678'
        }

    def validate(self):
        constants = self._constants()
        missing_keys = set(self.Key.all) - set(constants.keys())
        extra_keys = set(constants.keys()) - set(self.Key.all)
        assert not missing_keys, f"Missing keys: {missing_keys}"
        assert not extra_keys, f"Unexpected keys: {extra_keys}"

    @abstractmethod
    def save(self):
        ...

TBase = TypeVar('TBase', bound=Base)


def dispatch(cmd: Cmd, model_number: ModelNumber_t):
    if cmd == Cmd.GATEWAY:
        from . import gateway
        gateway.Default().save()
    elif cmd == Cmd.FIRMWARE:
        from . import firmware
        if model_number == firmware.Default.MODEL_NUMBER:
            firmware.Default().save()
        else:
            raise ValueError(f'Invalid model number: {model_number}.')
    else:
        raise ValueError(f'Invalid sub-cmd: {cmd}.')

