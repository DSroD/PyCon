"""RCON packet tests."""
# pylint: disable=missing-class-docstring

import unittest

from models.server import Server
from rcon.packets import (
    LoginPacket,
    CommandPacket,
    CommandEndPacket,
    next_packet,
    LoginSuccessResponse,
    InvalidPasswordResponse,
    CommandResponse, encoding
)
from tests.utils import PacketProvider


class PacketTest(unittest.IsolatedAsyncioTestCase):
    def test_login_packet_encoding(self):
        """Tests login packet encoding."""
        packet = LoginPacket("pwd", 1)
        encoded = packet.encode(encoding(Server.Type.MINECRAFT_SERVER))

        request_id = b"\x01\x00\x00\x00"  # 1
        packet_type = b"\x03\x00\x00\x00"  # 3 - login packet
        payload = b"\x70\x77\x64"  # pwd - utf-8 encoded
        padding = b"\x00\x00"  # 2 null bytes
        length = b"\x0D\x00\x00\x00"  # 13 - total number of bytes above

        body = length + request_id + packet_type + payload + padding

        self.assertEqual(body, encoded)

    def test_command_packet_encoding(self):
        """Tests command packet encoding."""
        packet = CommandPacket("help", 5)
        encoded = packet.encode(encoding(Server.Type.MINECRAFT_SERVER))

        request_id = b"\x05\x00\x00\x00"  # 5
        packet_type = b"\x02\x00\x00\x00"  # 2 - command packet
        payload = b"\x68\x65\x6c\x70"  # help - utf-8 encoded
        padding = b"\x00\x00"
        length = b"\x0E\x00\x00\x00"

        body = length + request_id + packet_type + payload + padding

        self.assertEqual(body, encoded)

    def test_command_end_encoding(self):
        """Tests command end packet encoding."""
        packet = CommandEndPacket(6)
        encoded = packet.encode(encoding(Server.Type.MINECRAFT_SERVER))

        request_id = b"\x06\x00\x00\x00"  # 6
        packet_type = b"c\x00\x00\x00"  # 99 - command end is "invalid" packet
        padding = b"\x00\x00"
        length = b"\x0A\x00\x00\x00"

        body = length + request_id + packet_type + padding

        self.assertEqual(body, encoded)

    async def test_success_login_packet_decode(self):
        """Tests decoding of a successful login response packet."""
        request_id = b"\x08\x00\x00\x00"
        packet_type = b"\x02\x00\x00\x00"
        padding = b"\x00\x00"
        length = b"\x0A\x00\x00\x00"

        content = PacketProvider(length + request_id + packet_type + padding)
        packet = await next_packet(content)

        self.assertEqual(packet, LoginSuccessResponse(8))

    async def test_failure_login_packet_decode(self):
        """Tests decoding of a failed login response packet."""
        request_id = b"\xFF\xFF\xFF\xFF"  # Request id -1 -> failure
        packet_type = b"\x02\x00\x00\x00"  # Packet type 2
        padding = b"\x00\x00"
        length = b"\x0A\x00\x00\x00"

        content = PacketProvider(length + request_id + packet_type + padding)
        packet = await next_packet(content)

        self.assertEqual(packet, InvalidPasswordResponse())

    async def test_command_packet_decode(self):
        """Tests decoding of a command response packet."""
        request_id = b"\x07\x00\x00\x00"  # 7
        packet_type = b"\x00\x00\x00\x00"   # 0
        padding = b"\x00\x00"
        payload = b"\x73\x75\x63\x63\x65\x73\x73"  # payload contains string "success" in this case
        length = b"\x11\x00\x00\x00"

        content = PacketProvider(length + request_id + packet_type + payload + padding)
        packet = await next_packet(content)

        self.assertEqual(packet, CommandResponse(7, payload))
