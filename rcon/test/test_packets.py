import asyncio
import unittest

from models.server import Server
from rcon.encoding import encoding
from rcon.packets import LoginPacket, CommandPacket, CommandEndPacket, next_packet, LoginSuccessResponse, \
    LoginFailedResponse, CommandResponse


class PacketTest(unittest.IsolatedAsyncioTestCase):
    def test_login_packet_encoding(self):
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
        packet = CommandEndPacket(6)
        encoded = packet.encode(encoding(Server.Type.MINECRAFT_SERVER))

        request_id = b"\x06\x00\x00\x00"  # 6
        packet_type = b"\x02\x00\x00\x00"  # 2 - command end is empty command packet
        padding = b"\x00\x00"
        length = b"\x0A\x00\x00\x00"

        body = length + request_id + packet_type + padding

        self.assertEqual(body, encoded)

    async def test_success_login_packet_decode(self):
        request_id = b"\x08\x00\x00\x00"
        packet_type = b"\x02\x00\x00\x00"
        padding = b"\x00\x00"
        length = b"\x0A\x00\x00\x00"

        content = PacketProvider(length + request_id + packet_type + padding)
        packet = await next_packet(content)

        self.assertEqual(packet, LoginSuccessResponse(8))

    async def test_failure_login_packet_decode(self):
        request_id = b"\xFF\xFF\xFF\xFF"  # Request id -1 -> failure
        packet_type = b"\x02\x00\x00\x00"  # Packet type 2
        padding = b"\x00\x00"
        length = b"\x0A\x00\x00\x00"

        content = PacketProvider(length + request_id + packet_type + padding)
        packet = await next_packet(content)

        self.assertEqual(packet, LoginFailedResponse())

    async def test_command_packet_decode(self):
        request_id = b"\x07\x00\x00\x00"  # 7
        packet_type = b"\x00\x00\x00\x00"   # 0
        padding = b"\x00\x00"
        payload = b"\x73\x75\x63\x63\x65\x73\x73"  # payload contains string "success" in this case
        length = b"\x11\x00\x00\x00"

        content = PacketProvider(length + request_id + packet_type + payload + padding)
        packet = await next_packet(content)

        self.assertEqual(packet, CommandResponse(7, payload))


class PacketProvider:
    def __init__(self, packet: bytes):
        self._packet = packet

    def __call__(self, n: int):
        return self._get(n)

    async def _get(self, n: int):
        if n > len(self._packet):
            raise asyncio.IncompleteReadError(self._packet, n)
        res = self._packet[:n]
        self._packet = self._packet[n:]
        return res
