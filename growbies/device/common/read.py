import ctypes
import logging
from ctypes import sizeof
from enum import IntEnum
from typing import Any

from prettytable import PrettyTable

from .common import BaseStructure
from growbies.constants import INDENT, UINT8_MAX
from growbies.service.common import ServiceCmdError
from growbies.utils.report import format_dropped_bytes
from growbies.utils.timestamp import get_utc_iso_ts_str

logger = logging.getLogger(__name__)

class EndpointType(IntEnum):
    MASS_SENSOR = 0
    MASS = 1
    MASS_FILTERED_SAMPLES = 2
    TEMPERATURE_SENSOR = 3
    TEMPERATURE = 4
    TEMPERATURE_FILTERED_SAMPLES = 5
    TARE_CRC = 6
    UNKNOWN = UINT8_MAX

    @property
    def type(self):
        if self.value in (self.MASS_SENSOR, self.MASS, self.TEMPERATURE_SENSOR, self.TEMPERATURE):
            return ctypes.c_float
        elif self.value in (self.MASS_FILTERED_SAMPLES, self.TEMPERATURE_FILTERED_SAMPLES):
            return ctypes.c_uint8
        elif self.value == self.TARE_CRC:
            return ctypes.c_uint16
        else:
            return bytes

    def __str__(self):
        return self.name

class TLVHdr(BaseStructure):
    TYPE_FIELD_CTYPE = ctypes.c_uint8
    class Field(BaseStructure.Field):
        TYPE = '_type'
        LENGTH = '_length'

    _fields_ = [
        (Field.TYPE, TYPE_FIELD_CTYPE),
        (Field.LENGTH, ctypes.c_uint8)
    ]

    @property
    def type(self) -> EndpointType | int:
        val = getattr(self, self.Field.TYPE)
        try:
            return EndpointType(getattr(self, self.Field.TYPE))
        except ValueError:
            return val

    @type.setter
    def type(self, value: EndpointType):
        setattr(self, self.Field.TYPE, value)

    @property
    def length(self) -> int:
        return getattr(self, self.Field.LENGTH)

    @length.setter
    def length(self, value: int):
        setattr(self, self.Field.LENGTH, value)

class DataPoint:
    def __init__(self, buf: bytearray | memoryview):
        self._type_vals = dict()

        if isinstance(buf, memoryview):
            buf = bytearray(buf)

        offset = 0
        while offset <= len(buf) - sizeof(TLVHdr):
            hdr = TLVHdr.from_buffer(buf, offset)
            offset += sizeof(hdr)

            try:
                etype = EndpointType(hdr.type)
                if etype == EndpointType.UNKNOWN:
                    etype = None
            except ValueError:
                etype = None


            if etype is None:
                offset -= sizeof(hdr)
                datalen = sizeof(hdr) + hdr.length
                if EndpointType.UNKNOWN not in self._type_vals:
                    self._type_vals[EndpointType.UNKNOWN] = list()
                self._type_vals[EndpointType.UNKNOWN].append(buf[offset:offset+datalen])
                offset += datalen
            else:
                klass = etype.type
                required = sizeof(klass)

                if offset + required > len(buf):
                    raise ServiceCmdError(f'Buffer underflow while deserializing to '
                                          f'{DataPoint.__qualname__}. Endpoint type {hdr.type} '
                                          f'requires {required} bytes starting at offset '
                                          f'{offset}. Length of buffer is {len(buf)} bytes.')
                else:
                    if hdr.type not in self._type_vals:
                        self._type_vals[hdr.type] = list()
                    for ii in range(hdr.length // required):
                        self._type_vals[hdr.type].append(klass.from_buffer(buf, offset))
                        offset += required

    def _get_table(self) -> PrettyTable:
        mass_sensors = self._type_vals.get(EndpointType.MASS_SENSOR, [])
        mass_sensors = [f'{x.value:.2f}' for x in mass_sensors]
        mass_sensors = f'[{", ".join(mass_sensors)}]'
        mass_errors = self._type_vals.get(EndpointType.MASS_FILTERED_SAMPLES, [])
        mass_errors = [x.value for x in mass_errors]
        total_mass = self._type_vals.get(EndpointType.MASS,
                                         [EndpointType.MASS.type(0.0)])[0].value
        total_mass = f'{total_mass:.2f}'
        temp_sensors = self._type_vals.get(EndpointType.TEMPERATURE_SENSOR, [])
        temp_sensors = [f'{x.value:.2f}' for x in temp_sensors]
        temp_sensors = f'[{", ".join(temp_sensors)}]'
        temp_errors = self._type_vals.get(EndpointType.TEMPERATURE_FILTERED_SAMPLES, [])
        temp_errors = [x.value for x in temp_errors]
        avg_temp = self._type_vals.get(EndpointType.TEMPERATURE,
                                       [EndpointType.TEMPERATURE.type(0.0)])[0].value
        avg_temp = f'{avg_temp:.2f}'
        tare_crc = (self._type_vals.get(EndpointType.TARE_CRC,
                                        [EndpointType.TARE_CRC.type(0)])[0].value)
        tare_crc = f'0x{tare_crc:04X}'

        table = PrettyTable(title = 'DataPoint')
        table.field_names = ['Field', 'Value']
        for field in table.field_names:
            table.align[field] = 'l'
        table.add_row(['Mass (g)', total_mass])
        table.add_row(['Mass Sensors (DAC)', mass_sensors])
        table.add_row(['Mass Errors', mass_errors])
        table.add_row(['Temperature (*C)', avg_temp])
        table.add_row(['Temperature Sensors (DAC)', temp_sensors])
        table.add_row(['Temperature Errors', temp_errors])
        table.add_row(['Timestamp', get_utc_iso_ts_str(timespec='seconds')])
        table.add_row(['Tare CRC', tare_crc])

        return table


    def _get_unknown_endpoint_str(self) -> str:
        unknown_bufs = self._type_vals.get(EndpointType.UNKNOWN, [])
        str_list = list()
        if unknown_bufs:
            str_list.append('Unknown Endpoints:')
            for buf in unknown_bufs:
                str_list += [f'{INDENT}{format_dropped_bytes(buf)}']
        return '\n'.join(str_list)

    def __str__(self) -> str:
        str_list = [
            str(self._get_table()),
        ]
        unknown_endpoint_str = self._get_unknown_endpoint_str()
        if unknown_endpoint_str:
            str_list.append(unknown_endpoint_str)
        return '\n'.join(str_list)

    @property
    def endpoints(self) -> dict[EndpointType, Any]:
        return self._type_vals
