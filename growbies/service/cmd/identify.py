import logging

from ..common import BaseServiceCmd, PositionalParam, ServiceCmd, ServiceCmdError, SUBCMD
from ..serials_to_devices import serials_to_devices
from growbies.device.cmd import GetIdentifyDeviceCmd, SetIdentifyDeviceCmd
from growbies.device.common import identify as id_mod
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

from argparse import ArgumentParser, Namespace

def _field_to_param(field: str):
    return f'--{id_mod.Identify1.Field.lstrip(field)}'

class Param:
    INIT = 'init'

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
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
    cmd_kw: dict
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.ID, **kw)

def get_or_set(cmd: IdServiceCmd) -> id_mod.TIdentify:
    pool = get_pool()

    serial = cmd.cmd_kw.pop(PositionalParam.SERIAL)
    init = cmd.cmd_kw.pop(Param.INIT, None)

    device = serials_to_devices(serial)[0]

    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    identify: id_mod.TIdentify = worker.cmd(GetIdentifyDeviceCmd())

    if all(value is None for value in cmd.cmd_kw.values()):
        return identify

    if init:
        # Setting magic to the non-magic number will initialize the structure in non-volatile
        # memory, on device, with default values.
        identify.hdr.magic = 0
    else:
        for key, val in cmd.cmd_kw.items():
            if getattr(identify, key) is None:
                raise ServiceCmdError(f'Identify version {identify.hdr.version} does not support the '
                                      f'"{key}" field.')
            if val is not None:
                setattr(identify, key, val)

    _ = worker.cmd(SetIdentifyDeviceCmd(payload=identify))
    return worker.cmd(GetIdentifyDeviceCmd())

def get_service_cmd(ns: Namespace) -> IdServiceCmd:
    partial_serial = getattr(ns, PositionalParam.SERIAL)
    delattr(ns, PositionalParam.SERIAL)
    device = serials_to_devices(partial_serial)[0]
    return IdServiceCmd(serial=device.serial, kw=vars(ns))