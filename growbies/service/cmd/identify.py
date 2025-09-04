import logging

from ..common import (BaseServiceCmd, PositionalParam, serials_to_devices, ServiceCmd,
                      ServiceCmdError)
from growbies.device.cmd import GetIdentifyDeviceCmd, SetIdentifyDeviceCmd
from growbies.device.common import identify as id_mod
from growbies.utils.types import Serial_t
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

from argparse import ArgumentParser, Namespace


def _field_to_param(field: str):
    return f'--{id_mod.Identify1.Field.lstrip(field)}'
    # return f'--{Identify.Field.lstrip(field).replace("_", "-")}'

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))

    parser.add_argument(_field_to_param(id_mod.Identify.Field.MODEL_NUMBER),
                        default=None, type=str)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.MASS_SENSOR_COUNT),
                        default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.MASS_SENSOR_TYPE),
                        choices=[None] + list(id_mod.MassSensorType), default=None,
                        type=id_mod.MassSensorType)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.TEMPERATURE_SENSOR_COUNT),
                        default=None, type=int)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.TEMPERATURE_SENSOR_TYPE),
                        choices=[None] + list(id_mod.MassSensorType), default=None,
                        type=id_mod.TemperatureSensorType)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.PCBA),
                        choices=[None] + list(id_mod.PcbaType), default=None, type=id_mod.PcbaType)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.WIRELESS),
                        choices=[None] + list(id_mod.WirelessType), default=None,
                        type=id_mod.WirelessType)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.BATTERY),
                        choices=[None] + list(id_mod.BatteryType), default=None,
                        type=id_mod.BatteryType)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.DISPLAY),
                        choices=[None] + list(id_mod.DisplayType), default=None,
                        type=id_mod.DisplayType)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.LED),
                        choices=[None] + list(id_mod.LedType), default=None, type=id_mod.LedType)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.FRAME),
                        choices=[None] + list(id_mod.FrameType), default=None,
                        type=id_mod.FrameType)
    parser.add_argument(_field_to_param(id_mod.Identify.Field.FOOT),
                        choices=[None] + list(id_mod.FootType), default=None, type=id_mod.FootType)

class IdServiceCmd(BaseServiceCmd):
    serial: Serial_t
    device_cmd_kw: dict
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.ID, **kw)

def get_or_set(cmd: IdServiceCmd) -> id_mod.TIdentify:
    pool = get_pool()

    device = serials_to_devices(cmd.serial)[0]

    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    identify: id_mod.TIdentify = worker.cmd(GetIdentifyDeviceCmd())

    if all(value is None for value in cmd.device_cmd_kw.values()):
        return identify

    for key, val in cmd.device_cmd_kw.items():
        if getattr(identify, key) is None:
            raise ServiceCmdError(f'Identify version {identify.hdr.version} does not support the '
                                  f'"{key}" field.')
        if val is not None:
            setattr(identify, key, val)

    cmd = SetIdentifyDeviceCmd(payload=identify)

    _ = worker.cmd(cmd)

    return worker.cmd(GetIdentifyDeviceCmd())

def get_service_cmd(ns: Namespace) -> IdServiceCmd:
    partial_serial = getattr(ns, PositionalParam.SERIAL)
    delattr(ns, PositionalParam.SERIAL)
    device = serials_to_devices(partial_serial)[0]
    return IdServiceCmd(serial=device.serial, kw=vars(ns))