from typing import Optional

from argparse import ArgumentParser

from ..common import ServiceCmd, PositionalParam, ServiceCmdError
from ..serials_to_devices import serials_to_devices
from growbies.device.cmd import GetIdentifyDeviceCmd, SetIdentifyDeviceCmd
from growbies.device.common import identify as id_mod
from growbies.device.common import internal_to_external_field
from growbies.worker.pool import get_pool

class Param:
    INIT = 'init'

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.SERIAL_NUMBER)}',
                        default=None, type=str)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.MODEL_NUMBER)}',
                        default=None, type=str)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.MASS_SENSOR_COUNT)}',
                        default=None,
                        type=int)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.MASS_SENSOR_TYPE)}',
                        choices=[None] + list(id_mod.MassSensorType), default=None, type=int)
    parser.add_argument(
        f'--{internal_to_external_field(id_mod.Identify.Field.TEMPERATURE_SENSOR_COUNT)}',
        default=None, type=int)
    parser.add_argument(
        f'--{internal_to_external_field(id_mod.Identify.Field.TEMPERATURE_SENSOR_TYPE)}',
        choices=[None] + list(id_mod.MassSensorType), default=None, type=int)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.PCBA)}',
                        choices=[None] + list(id_mod.PcbaType), default=None, type=int)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.WIRELESS)}',
                        choices=[None] + list(id_mod.WirelessType), default=None, type=int)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.BATTERY)}',
                        choices=[None] + list(id_mod.BatteryType), default=None, type=int)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.DISPLAY)}',
                        choices=[None] + list(id_mod.DisplayType), default=None, type=int)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.LED)}',
                        choices=[None] + list(id_mod.LedType), default=None, type=int)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.FRAME)}',
                        choices=[None] + list(id_mod.FrameType), default=None, type=int)
    parser.add_argument(f'--{internal_to_external_field(id_mod.Identify.Field.FOOT)}',
                        choices=[None] + list(id_mod.FootType), default=None, type=int)

def _init(worker):
    cmd = SetIdentifyDeviceCmd(init=True)
    cmd.init = True
    _ = worker.cmd(cmd)

def identify(cmd: ServiceCmd) -> Optional[id_mod.TIdentify]:
    pool = get_pool()
    serial = cmd.kw.pop(PositionalParam.SERIAL)
    init = cmd.kw.pop(Param.INIT)
    device = serials_to_devices(serial)[0]
    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    if init:
        _init(worker)
        return None

    ident: id_mod.TIdentify = worker.cmd(GetIdentifyDeviceCmd())

    if all(value is None for value in cmd.kw.values()):
        return ident

    for key, val in cmd.kw.items():
        if getattr(ident, key) is None:
            _, version = ident.get_op_and_version()
            raise ServiceCmdError(f'Identify version {version} does not support the '
                                  f'"{key}" field.')
        if val is not None:
            setattr(ident, key, val)

    cmd = SetIdentifyDeviceCmd()
    cmd.identify = ident
    _ = worker.cmd(cmd)
    return None
