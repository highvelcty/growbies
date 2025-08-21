from typing import cast
import ctypes

from growbies.intf.common import Packet
from growbies.intf import datalink, network

from .base import BaseTest, BaseMockArduino


class MockArduino(BaseMockArduino, network.Network):
    pass


class TestArduinoNetwork(BaseTest):

    @classmethod
    def make_mock_arduino(cls):
        return MockArduino()

    def test__send_packet(self):
        buf = bytearray(Packet.MIN_SIZE_IN_BYTES + 4)
        packet = Packet.make(buf)
        self._arduino_serial._send_packet(buf)

        self.assertEqual(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0', self._arduino_serial.written)

        packet.data[0] = datalink.Slip.END
        self._arduino_serial.reset()
        self._arduino_serial._send_packet(buf)
        self.assertEqual(b'\x00\x00\x00\x00\xdb\xdc\x00\x00\x00\xdb\xdc\x00\xc0',
                         self._arduino_serial.written)

        packet.data[0] = datalink.Slip.ESC
        self._arduino_serial.reset()
        self._arduino_serial._send_packet(buf)
        self.assertEqual(b'\x00\x00\x00\x00\xdb\xdd\x00\x00\x00\xdb\xdd\x00\xc0',
                         self._arduino_serial.written)

        packet.data[0] = 0xFF
        self._arduino_serial.reset()
        self._arduino_serial._send_packet(buf)
        self.assertEqual(b'\x00\x00\x00\x00\xff\x00\x00\x00\xff\x00\xc0',
                         self._arduino_serial.written)

        packet.data[0] = 0x01
        packet.data[1] = 0x02
        packet.data[2] = 0x03
        packet.data[3] = 0x04
        self._arduino_serial.reset()
        self._arduino_serial._send_packet(buf)
        self.assertEqual(b'\x00\x00\x00\x00\x01\x02\x03\x04\n\x00\xc0',
                         self._arduino_serial.written)

        for payload_bytes in (b'\x00', b'\x01', b'\xff', b'\x02\x03',
                         bytes((datalink.Slip.END,)), bytes((datalink.Slip.ESC,))):

            packet = Packet.make(Packet.MIN_SIZE_IN_BYTES + len(payload_bytes))
            buf = memoryview(cast(bytes, packet)).cast('B')
            for payload_idx, payload_byte in enumerate(payload_bytes):
                packet.data[payload_idx] = payload_byte

            self._arduino_serial.reset()
            self._arduino_serial._slip_reset_recv_state()
            self._arduino_serial._send_packet(buf)

            decode_passed = self._arduino_serial._slip_decode_frame(
                self._arduino_serial.written)
            self.assertTrue(decode_passed)
            decoded_buf = memoryview(self._arduino_serial._recv_buf).cast('B')[
                          :self._arduino_serial._recv_buf_idx -
                           network.Network.CHECKSUM_BYTES]
            packet = Packet.make(decoded_buf)
            payload_offset = ctypes.sizeof(packet.header)
            payload = memoryview(cast(bytes, packet)).cast('B')[payload_offset:payload_offset +
                                                                               len(packet.data)]
            self.assertEqual(bytes(payload), payload_bytes)