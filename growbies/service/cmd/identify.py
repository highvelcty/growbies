from typing import Optional
import logging

from ..common import ServiceCmd, PositionalParam, ServiceCmdError
from ..serials_to_devices import serials_to_devices
from growbies.device.cmd import GetIdentifyDeviceCmd, SetIdentifyDeviceCmd
from growbies.device.common import identify as id_mod
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

from argparse import ArgumentParser

def _field_to_param(field: str):
    return f'--{id_mod.Identify1.Field.lstrip(field)}'

class Param:
    INIT = 'init'

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
    parser.add_argument(_field_to_param(id_mod.Identify.Field.SERIAL_NUMBER), default=None,
                        type=str)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.MODEL_NUMBER), default=None, type=str)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.MASS_SENSOR_COUNT), default=None,
                        type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.MASS_SENSOR_TYPE),
                        choices=[None] + list(id_mod.MassSensorType), default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.TEMPERATURE_SENSOR_COUNT),
                        default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.TEMPERATURE_SENSOR_TYPE),
                        choices=[None] + list(id_mod.MassSensorType), default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.PCBA),
                        choices=[None] + list(id_mod.PcbaType), default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.WIRELESS),
                        choices=[None] + list(id_mod.WirelessType), default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.BATTERY),
                        choices=[None] + list(id_mod.BatteryType), default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.DISPLAY),
                        choices=[None] + list(id_mod.DisplayType), default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.LED),
                        choices=[None] + list(id_mod.LedType), default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.FRAME),
                        choices=[None] + list(id_mod.FrameType), default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.FOOT),
                        choices=[None] + list(id_mod.FootType), default=None, type=int)

def _init(worker):
    cmd = SetIdentifyDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def get_or_set(cmd: ServiceCmd) -> Optional[id_mod.TIdentify]:
    pool = get_pool()
    serial = cmd.kw.pop(PositionalParam.SERIAL)
    init = cmd.kw.pop(Param.INIT)
    device = serials_to_devices(serial)[0]
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    if init:
        return _init(worker)

    identify: id_mod.TIdentify = worker.cmd(GetIdentifyDeviceCmd())

    if all(value is None for value in cmd.kw.values()):
        return identify

    for key, val in cmd.kw.items():
        if getattr(identify, key) is None:
            raise ServiceCmdError(f'Identify version {identify.hdr.version} does not support the '
                                  f'"{key}" field.')
        if val is not None:
            setattr(identify, key, val)

    cmd = SetIdentifyDeviceCmd()
    cmd.identify = identify
    _ = worker.cmd(cmd)

    return worker.cmd(GetIdentifyDeviceCmd())
