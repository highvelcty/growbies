from growbies.arduino import datalink

from .base import BaseMockArduino as BaseMockArduino, BaseTest

class MockArduino(BaseMockArduino, datalink.ArduinoDatalink):
    pass


class TestArduinoDatalink(BaseTest):
    @classmethod
    def make_mock_arduino(cls):
        return MockArduino()


    def test__slip_encode_byte(self):
        self._arduino_serial._slip_send_byte(datalink.Slip.END)
        self.assertEqual(bytes((datalink.Slip.ESC, datalink.Slip.ESC_END)),
                         self._arduino_serial.written)

        self._arduino_serial.reset()
        self._arduino_serial.reset()
        self._arduino_serial._slip_send_byte(datalink.Slip.ESC)
        self.assertEqual(bytes((datalink.Slip.ESC, datalink.Slip.ESC_ESC)),
                         self._arduino_serial.written)

        test_bytes = (0x00, 0x01, 0x35, 0xff)
        for byte in test_bytes:
            self._arduino_serial.reset()
            self._arduino_serial._slip_send_byte(byte)
            self.assertEqual(bytes((byte,)), self._arduino_serial.written)

        with self.assertRaises(ValueError):
            self._arduino_serial._slip_send_byte(0x100)

    def test__reset_slip_recv_state(self):
        self._arduino_serial._recv_buf_idx = 1
        self._arduino_serial._within_escape = True
        self._arduino_serial._slip_reset_recv_state()
        self.assertEqual(0, self._arduino_serial._recv_buf_idx)
        self.assertEqual(False, self._arduino_serial._within_escape)

    def test__slip_decode_frame(self):
        self._arduino_serial._slip_reset_recv_state()
        decode_passed = self._arduino_serial._slip_decode_frame(b'\x00\x01\x00\x01\xC0')
        self.assertTrue(decode_passed)

        self._arduino_serial._slip_reset_recv_state()
        decode_passed = self._arduino_serial._slip_decode_frame(b'\x00\x01\x00\x01\xC0')
        self.assertTrue(decode_passed)

        self._arduino_serial._slip_reset_recv_state()
        decode_passed = self._arduino_serial._slip_decode_frame(b'\x00')
        self.assertFalse(decode_passed)

        self._arduino_serial._slip_reset_recv_state()
        buf = b''.join(((b'\x00' * self._arduino_serial.RECV_BUF_BYTES), b'\xC0'))
        decode_passed = self._arduino_serial._slip_decode_frame(buf)
        self.assertTrue(decode_passed)

        self._arduino_serial._slip_reset_recv_state()
        buf = b'\x00' * len(self._arduino_serial._recv_buf)
        decode_passed = self._arduino_serial._slip_decode_frame(buf)
        self.assertFalse(decode_passed)
