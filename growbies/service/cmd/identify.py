import logging

from growbies.service.cli import serials_to_devices
from growbies.service.cmd.structs import IdServiceCmd
from growbies.service.resp.structs import ServiceCmdError
from growbies.intf.cmd import GetIdentifyDeviceCmd, SetIdentifyDeviceCmd
from growbies.intf.common import TIdentify
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

from argparse import ArgumentParser, Namespace

from .common import PositionalParam, serials_to_devices
from growbies.intf.common.identify import *
from growbies.service.cmd.structs import IdServiceCmd

def _field_to_param(field: str):
    return f'--{Identify1.Field.lstrip(field)}'
    # return f'--{Identify.Field.lstrip(field).replace("_", "-")}'

def make(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIAL, type=str,
                            help=PositionalParam.get_help_str(PositionalParam.SERIAL))

    parser.add_argument(_field_to_param(Identify.Field.MODEL_NUMBER),
                        default=None, type=str)
    parser.add_argument(_field_to_param(Identify.Field.MASS_SENSOR_COUNT),
                        default=None, type=int)
    parser.add_argument(_field_to_param(Identify.Field.MASS_SENSOR_TYPE),
                        choices=[None] + list(MassSensorType), default=None, type=MassSensorType)
    parser.add_argument(_field_to_param(Identify.Field.TEMPERATURE_SENSOR_COUNT),
                        default=None, type=int)
    parser.add_argument(_field_to_param(Identify.Field.TEMPERATURE_SENSOR_TYPE),
                        choices=[None] + list(MassSensorType), default=None,
                        type=TemperatureSensorType)
    parser.add_argument(_field_to_param(Identify.Field.PCBA),
                        choices=[None] + list(PcbaType), default=None, type=PcbaType)
    parser.add_argument(_field_to_param(Identify.Field.WIRELESS),
                        choices=[None] + list(WirelessType), default=None, type=WirelessType)
    parser.add_argument(_field_to_param(Identify.Field.BATTERY),
                        choices=[None] + list(BatteryType), default=None, type=BatteryType)
    parser.add_argument(_field_to_param(Identify.Field.DISPLAY),
                        choices=[None] + list(DisplayType), default=None, type=DisplayType)
    parser.add_argument(_field_to_param(Identify.Field.LED),
                        choices=[None] + list(LedType), default=None, type=LedType)
    parser.add_argument(_field_to_param(Identify.Field.FRAME),
                        choices=[None] + list(FrameType), default=None, type=FrameType)
    parser.add_argument(_field_to_param(Identify.Field.FOOT),
                        choices=[None] + list(FootType), default=None, type=FootType)

def get_service_cmd(ns: Namespace) -> IdServiceCmd:
    partial_serial = getattr(ns, PositionalParam.SERIAL)
    delattr(ns, PositionalParam.SERIAL)
    device = serials_to_devices(partial_serial)[0]
    return IdServiceCmd(serial=device.serial, kw=vars(ns))


class IdServiceCmd(BaseServiceCmd):
    serial: Serial_t
    device_cmd_kw: dict
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.ID, **kw)

def get_or_set(cmd: IdServiceCmd) -> TIdentify:
    pool = get_pool()

    device = serials_to_devices(cmd.serial)[0]

    try:
        worker = pool.workers[device.id]
    except KeyError:
        raise ServiceCmdError(f'Serial number "{device.serial}" is inactive.')

    identify: TIdentify = worker.cmd(GetIdentifyDeviceCmd())

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
