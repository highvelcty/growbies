from unittest import TestCase
import ctypes

from growbies.arduino.structs import command
from growbies.utils.bufstr import BufStr

class TestRespMassDataPoint(TestCase):
    def test(self):
        num_sensors = 4
        packet = command.Packet.make(ctypes.sizeof(command.PacketHeader) +
                                     ctypes.sizeof(command.MassDataPoint) * num_sensors)
        resp_mass_data_point = command.RespMassDataPoint.from_packet(packet)


        for sensor in resp_mass_data_point.sensor:
            print(BufStr(ctypes.string_at(
                ctypes.byref(sensor),
                ctypes.sizeof(sensor))))

        print(BufStr(ctypes.string_at(
            ctypes.byref(resp_mass_data_point),
            ctypes.sizeof(resp_mass_data_point))))
