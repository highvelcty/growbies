from unittest import TestCase
from unittest.mock import patch
import ctypes

from growbies.arduino import arduino_slip as a_slip
from growbies.arduino import structs


class MockWriteTracker:
    def __init__(self):
        self.written = b''

    def reset(self):
        self.written = b''

    def write(self, data):
        self.written += data


class TestSlip(TestCase):
    _arduino_serial = None
    _mock_write_tracker = MockWriteTracker()
    _patchers = []

    @classmethod
    def setUpClass(cls):
        cls._patchers.append(patch.object(a_slip.ArduinoSerial, '__init__', lambda _: None))
        cls._patchers.append(patch.object(a_slip.ArduinoSerial, 'write',
                                          cls._mock_write_tracker.write))

        for patcher in cls._patchers:
            patcher.start()

        cls._arduino_serial = a_slip.ArduinoSerial()

    @classmethod
    def tearDownClass(cls):
        for patcher in cls._patchers:
            patcher.stop()

    def setUp(self):
        self._mock_write_tracker.reset()

    def test__slip_encode_byte(self):
        self._arduino_serial._slip_send_byte(a_slip.Slip.END)
        self.assertEqual(bytes((a_slip.Slip.ESC, a_slip.Slip.ESC_END)),
                         self._mock_write_tracker.written)

        self._mock_write_tracker.reset()
        self._arduino_serial._slip_send_byte(a_slip.Slip.ESC)
        self.assertEqual(bytes((a_slip.Slip.ESC, a_slip.Slip.ESC_ESC)),
                         self._mock_write_tracker.written)

        test_bytes = (0x00, 0x01, 0x35, 0xff)
        for byte in test_bytes:
            self._mock_write_tracker.reset()
            self._arduino_serial._slip_send_byte(byte)
            self.assertEqual(bytes((byte,)), self._mock_write_tracker.written)

        with self.assertRaises(ValueError):
            self._arduino_serial._slip_send_byte(0x100)

    def test__slip_send_send_packet(self):
        buf = bytearray(structs.Packet.MIN_SIZE_IN_BYTES + 4)
        packet = structs.Packet.make(buf)
        self._arduino_serial._slip_send_packet(packet)
        self.assertEqual(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xc0',
                         self._mock_write_tracker.written)

        packet.data[0] = a_slip.Slip.END
        packet.update_checksum()
        self._mock_write_tracker.reset()
        self._arduino_serial._slip_send_packet(packet)
        self.assertEqual(b'\x00\x00\x00\x00\xdb\xdc\x00\x00\x00\xdb\xdc\x00\xc0',
                         self._mock_write_tracker.written)

        packet.data[0] = a_slip.Slip.ESC
        packet.update_checksum()
        self._mock_write_tracker.reset()
        self._arduino_serial._slip_send_packet(packet)
        self.assertEqual(b'\x00\x00\x00\x00\xdb\xdd\x00\x00\x00\xdb\xdd\x00\xc0',
                         self._mock_write_tracker.written)

        packet.data[0] = 0xFF
        packet.update_checksum()
        self._mock_write_tracker.reset()
        self._arduino_serial._slip_send_packet(packet)
        self.assertEqual(b'\x00\x00\x00\x00\xff\x00\x00\x00\xff\x00\xc0',
                         self._mock_write_tracker.written)

        packet.data[0] = 0x01
        packet.data[1] = 0x02
        packet.data[2] = 0x03
        packet.data[3] = 0x04
        packet.update_checksum()
        self._mock_write_tracker.reset()
        self._arduino_serial._slip_send_packet(packet)
        self.assertEqual(b'\x00\x00\x00\x00\x01\x02\x03\x04\n\x00\xc0',
                         self._mock_write_tracker.written)

    def test__reset_slip_recv_state(self):
        self._arduino_serial._recv_buf_idx = 1
        self._arduino_serial._within_escape = True
        self._arduino_serial._reset_slip_recv_state()
        self.assertEqual(0, self._arduino_serial._recv_buf_idx)
        self.assertEqual(False, self._arduino_serial._within_escape)

    def test__slip_decode_frame(self):
        self._arduino_serial._reset_slip_recv_state()
        frame = self._arduino_serial._slip_decode_frame(b'\x00\x01\x00\x01\xC0')
        self.assertEqual(b'\x00\x01\x00\x01', frame)

        self._arduino_serial._reset_slip_recv_state()
        frame = self._arduino_serial._slip_decode_frame(b'\x00\x01\x00\x01\xC0')
        self.assertEqual(b'\x00\x01\x00\x01', frame)

        self._arduino_serial._reset_slip_recv_state()
        frame = self._arduino_serial._slip_decode_frame(b'\x00')
        self.assertIsNone(frame)

        self._arduino_serial._reset_slip_recv_state()
        buf = b''.join(((b'\x00' * self._arduino_serial.RECV_BUF_BYTES), b'\xC0'))
        frame = self._arduino_serial._slip_decode_frame(buf)
        self.assertEqual(b'\x00' * self._arduino_serial.RECV_BUF_BYTES, frame)

        self._arduino_serial._reset_slip_recv_state()
        buf = b'\x00' * len(self._arduino_serial._recv_buf)
        frame = self._arduino_serial._slip_decode_frame(buf)
        self.assertIsNone(frame)

        hdr_len = ctypes.sizeof(structs.PacketHeader)
        packet = structs.Packet.make(structs.Packet.MIN_SIZE_IN_BYTES + 4)
        for payload_bytes in (b'\x00', b'\x01', b'\xff', b'\x02\x03',
                         bytes((a_slip.Slip.END,)), bytes((a_slip.Slip.ESC,))):

            for payload_idx, payload_byte in enumerate(payload_bytes):
                packet.data[payload_idx] = payload_byte

            self._mock_write_tracker.reset()
            self._arduino_serial._reset_slip_recv_state()
            self._arduino_serial._slip_send_packet(packet)
            decoded = self._arduino_serial._slip_decode_frame(self._mock_write_tracker.written)
            obs_bytes = bytes(decoded)[hdr_len:hdr_len+len(payload_bytes)]
            self.assertEqual(payload_bytes, obs_bytes)
