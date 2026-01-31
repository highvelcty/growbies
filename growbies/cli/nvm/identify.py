from argparse import ArgumentParser

from growbies.cli.common import Param as CommonParam
from growbies.device.common import identify as id_mod
from growbies.device.common import MassUnitsType

class Param:
    INIT = 'init'

def make_cli(parser: ArgumentParser):
    parser.add_argument(CommonParam.FUZZY_ID, nargs='?', default=None,
                        help=CommonParam.FUZZY_ID.help)
    parser.add_argument(f'--{Param.INIT}', action='store_true',
                        help='Set to initialize to default values.')
    parser.add_argument(f'--{id_mod.Identify.Field.SERIAL_NUMBER.public_name}',
                        default=None, type=str)
    parser.add_argument(f'--{id_mod.Identify.Field.MODEL_NUMBER.public_name}',
                        default=None, type=str)
    parser.add_argument(f'--{id_mod.Identify.Field.MASS_SENSOR_TYPE.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in id_mod.MassSensorType]) + '}',
                        choices=tuple(id_mod.MassSensorType), default=None, type=int)
    parser.add_argument(
        f'--{id_mod.Identify.Field.TEMPERATURE_SENSOR_TYPE.public_name}',
        metavar='{' + ','.join(
            [f'{x.value}={x.name}' for x in id_mod.TemperatureSensorType]) + '}',
        choices=tuple(id_mod.MassSensorType), default=None, type=int)
    parser.add_argument(f'--{id_mod.Identify.Field.PCBA.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in id_mod.PcbaType]) + '}',
                        choices=tuple(id_mod.PcbaType), default=None, type=int)
    parser.add_argument(f'--{id_mod.Identify.Field.WIRELESS.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in id_mod.WirelessType]) + '}',
                        choices=tuple(id_mod.WirelessType), default=None, type=int)
    parser.add_argument(f'--{id_mod.Identify.Field.BATTERY.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in id_mod.BatteryType]) + '}',
                        choices=tuple(id_mod.BatteryType), default=None, type=int)
    parser.add_argument(f'--{id_mod.Identify.Field.DISPLAY.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in id_mod.DisplayType]) + '}',
                        choices=tuple(id_mod.DisplayType), default=None, type=int)
    parser.add_argument(f'--{id_mod.Identify.Field.LED.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in id_mod.LedType]) + '}',
                        choices=tuple(id_mod.LedType), default=None, type=int)
    parser.add_argument(f'--{id_mod.Identify.Field.FRAME.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in id_mod.FrameType]) + '}',
                        choices=tuple(id_mod.FrameType), default=None, type=int)
    parser.add_argument(f'--{id_mod.Identify.Field.FOOT.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in id_mod.FootType]) + '}',
                        choices=tuple(id_mod.FootType), default=None, type=int)
    name = id_mod.Identify.Field.FLIP.public_name
    parser.add_argument(f'--{name}', dest=name, action='store_true',
                        help=f'Turn on remote flip. See also, --no-{name}')
    parser.add_argument(f'--no-{name}', dest=name, action='store_false',
                        help=f'Turn off remote flip. See also, --{name}')
    parser.set_defaults(flip=None)
    parser.set_defaults(no_flip=None)
    parser.add_argument(f'--{id_mod.Identify.Field.MASS_UNITS.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in MassUnitsType]) + '}',
                        choices=tuple(MassUnitsType), default=None, type=int)
    parser.add_argument(f'--{id_mod.Identify.Field.TEMPERATURE_UNITS.public_name}',
                        metavar='{' + ','.join(
                            [f'{x.value}={x.name}' for x in id_mod.TemperatureUnitsType]) + '}',
                        choices=tuple(id_mod.TemperatureUnitsType), default=None, type=int)
    parser.add_argument(f'--{id_mod.Identify.Field.CONTRAST.public_name}',
                        default=None, type=int,
                        help='Set the display contrast (0-255).')
    parser.add_argument(f'--{id_mod.Identify.Field.TELEMETRY_INTERVAL.public_name}',
                        default=None, type=float,
                        help='How often to transmit telemetry in seconds. 0.0 means "off".')
    parser.add_argument(f'--{id_mod.Identify.Field.SLEEP_TIMEOUT.public_name}',
                        default=None, type=float,
                        help='The interval, in seconds, to enter low power sleep mode. 0.0 means '
                             '"do not sleep".')
    parser.add_argument(f'--{id_mod.Identify.Field.AUTO_WAKE_INTERVAL.public_name}',
                        default=None, type=float,
                        help='The interval, in seconds, to poll for mass change for the auto-wake '
                             'feature.')
