from typing import cast
from typing_extensions import Buffer
from unittest import TestCase
import ctypes

from growbies.arduino import structs


class TestPacket(TestCase):
    def test(self):
        packet = structs.Packet.from_command(structs.CommandLoopback())

        self.assertTrue(packet.validate_checksum())
        self.assertEqual(packet.header.command, packet.Command.LOOPBACK)
        self.assertEqual(packet.header.length, ctypes.sizeof(packet))

        resp: structs.RespLoopback = packet.get_payload()
        self.assertTrue(isinstance(resp, structs.RespLoopback))
        self.assertTrue(resp.is_valid())