import os
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, TypeVar, NewType
import shlex
import subprocess

from growbies.utils.types import ModelNumber_t

BASE_FILENAME = 'build_cfg'
CMD = 'cmd'

class EnvironVars(StrEnum):
    MODEL_NUMBER = 'MODEL_NUMBER'

    @property
    def value(self) -> str:
        return os.environ.get(self, Base.MODEL_NUMBER)

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

class Base(ABC):
    MODEL_NUMBER = 'Default'

    class Key:
        # noinspection PyNewType
        type_ = NewType('Key', str)
        all = tuple()

        @classmethod
        def value(cls, key: 'Base.Key.type_'):
            assert ValueError(key)

        @classmethod
        def validate(cls):
            for key in cls.all:
                _ = cls.value(key)

    def validate(self):
        self.Key.validate()

    @abstractmethod
    def save(self):
        ...

TBase = TypeVar('TBase', bound=Base)


def dispatch(cmd: Cmd):
    model_number = EnvironVars.MODEL_NUMBER.value
    if cmd == Cmd.GATEWAY:
        from . import gateway
        if model_number == gateway.Default.MODEL_NUMBER:
            gateway.Default().save()
        else:
            raise ValueError(f'Invalid gateway model number: {model_number}.')
    elif cmd == Cmd.FIRMWARE:
        from . import firmware
        if model_number == firmware.Default.MODEL_NUMBER:
            firmware.Default().save()
        elif model_number == firmware.Esp32c3.MODEL_NUMBER:
            firmware.Esp32c3().save()
        elif model_number == firmware.Mini.MODEL_NUMBER:
            firmware.Mini().save()
        elif model_number == firmware.Uno.MODEL_NUMBER:
            firmware.Uno().save()
        elif model_number == firmware.CircleEsp32c3.MODEL_NUMBER:
            firmware.CircleEsp32c3().save()
        elif model_number == firmware.SquareEsp32c3.MODEL_NUMBER:
            firmware.SquareEsp32c3().save()
        else:
            raise ValueError(f'Invalid model number: {model_number}.')
    else:
        raise ValueError(f'Invalid sub-cmd: {cmd}.')

def get_git_hash() -> str:
    cmd = 'git rev-parse --short HEAD'
    res = subprocess.run(shlex.split(cmd),
                         stdout=subprocess.PIPE,
                         text=True, check=True)
    return res.stdout.strip()
