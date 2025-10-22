from argparse import ArgumentParser

from growbies.cli.common import internal_to_external_field, PositionalParam
from growbies.device.common import identify as id_mod

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
    name = internal_to_external_field(id_mod.Identify.Field.FLIP)
    parser.add_argument(f'--{name}', dest=name, action='store_true',
                        help=f'Turn on display flip. See also, --no-{name}')
    parser.add_argument(f'--no-{name}', dest=name, action='store_false',
                        help=f'Turn off display flip. See also, --{name}')
    parser.set_defaults(flip=None)
