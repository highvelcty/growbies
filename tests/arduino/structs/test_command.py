from unittest import TestCase
import ctypes

from growbies.arduino.structs import command
from growbies.utils.bufstr import BufStr

class TestRespMassDataPoint(TestCase):

    def setUp(self):
        self.num_sensors = 4
        self.packet = command.Packet.make(ctypes.sizeof(command.PacketHeader) +
                                          ctypes.sizeof(command.MultiDataPoint) * self.num_sensors)
    def test(self):
        resp_mass_data_point = command.RespMultiDataPoint.from_packet(self.packet)

        self.assertEqual(ctypes.sizeof(self.packet),
                         ctypes.sizeof(resp_mass_data_point))



        # Test that multiple structures can be created.
        _ = command.RespMultiDataPoint.from_packet(self.packet)
