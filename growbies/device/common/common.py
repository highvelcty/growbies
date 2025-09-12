from typing import Any, Optional, TYPE_CHECKING, Union, NewType
import ctypes
import logging

if TYPE_CHECKING:
    from ..cmd import DeviceCmdOp
    from ..resp import DeviceRespOp

logger = logging.getLogger(__name__)

_INTERNAL_FIELD_NAME_DELINEATOR = '_'

class _StructUnionMixin:
    class Field: pass

    @classmethod
    def qualname(cls):
        return cls.__qualname__

    @classmethod
    def all_fields(cls) -> list[tuple[str, type[Any], int, int]]:
        """
        Returns a list of all fields in memory layout, including inherited fields.
        Derived class fields override base class fields with the same name.
        Each item is a tuple: (field_name, field_type, offset, size)
        """
        seen = dict()
        # Walk MRO from base -> derived
        for base in cls.__mro__[::-1]:
            if (issubclass(base, (ctypes.Structure, ctypes.Union)) and
                    hasattr(base, '_fields_') and base not in (ctypes.Structure, ctypes.Union)):
                #noinspection PyProtectedMember
                for field_name, field_type in base._fields_:
                    # override previous base field if derived redefines it
                    seen[field_name] = (field_name, field_type,
                                        getattr(cls, field_name).offset, ctypes.sizeof(field_type))

        # preserve order in memory layout
        return list(seen.values())

    def get_str(self, prefix: str = '', _str_list: Optional[list[str]] = None):
        if _str_list is None:
            _str_list = list()
        for field_name, field_type, field_offset, field_size in self.all_fields():
            external_name = internal_to_external_field(field_name)
            is_anonymous = field_name in getattr(self, '_anonymous_', [])
            if is_anonymous:
                next_name = f'{prefix}'
            else:
                next_name = f'{prefix}.{external_name}' if prefix else external_name
            if issubclass(field_type, (ctypes.Structure, ctypes.Union)):
                if not is_anonymous:
                    for next_str in getattr(self, external_name).get_str(next_name):
                        if next_str not in _str_list:
                            _str_list.append(next_str)
            else:
                next_str = (f'0x{field_offset:04X} '
                            f'{next_name}: '
                            f'{repr(getattr(self, external_name))}')
                if next_str not in _str_list:
                    _str_list.append(next_str)
                    
        return _str_list

    def __str__(self):
        return '\n'.join(self.get_str())

class BaseStructure(ctypes.Structure, _StructUnionMixin):
    _pack_ = 1

TBaseStructure = NewType('TBaseStructure', BaseStructure)

class BaseUnion(ctypes.Union, _StructUnionMixin): pass
TBaseUnion = NewType('TBaseUnion', BaseUnion)

class PacketHdr(BaseStructure):
    class Field(BaseStructure.Field):
        TYPE = '_type'
        ID = '_id'
        VERSION = 'version'

    _fields_ = [
        (Field.TYPE, ctypes.c_uint16),
        (Field.ID, ctypes.c_uint8),
        (Field.VERSION, ctypes.c_uint8)
    ]

    @property
    def id(self) -> int:
        return getattr(self, self.Field.ID)

    @id.setter
    def id(self, value: int):
        setattr(self, self.Field.ID, value)

    @property
    def type(self) -> Union['DeviceCmdOp', 'DeviceRespOp']:
        return getattr(self, self.Field.TYPE)

    @type.setter
    def type(self, value: ['DeviceCmdOp', 'DeviceRespOp']):
        setattr(self, self.Field.TYPE, value)

    @property
    def version(self) -> int:
        return getattr(self, self.Field.VERSION)

    @version.setter
    def version(self, val: int):
        setattr(self, self.Field.VERSION, val)

def internal_to_external_field(field: str):
    return field.lstrip(_INTERNAL_FIELD_NAME_DELINEATOR)
