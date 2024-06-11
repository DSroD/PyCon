"""RCON communication packets."""
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Awaitable

from models.server import Server


class OutgoingRconPacket(ABC):
    """Base class for outgoing RCON packets."""

    @property
    @abstractmethod
    def _type(self) -> int:
        pass

    @property
    @abstractmethod
    def _request_id(self) -> int:
        pass

    @property
    @abstractmethod
    def _payload(self) -> str:
        """
        According to wiki.vg, for minecraft servers there might be maximal packet length of 1446.

        TODO: investigate
        """

    def encode(self, payload_encoding: str):
        """
        Encodes outgoing RCON packet.

        :param payload_encoding: Encoding to use
        :return: Encoded bytes
        """
        identifier_part = struct.pack("<ii", self._request_id, self._type)
        # Encoded message (null terminated) and padding byte
        message_part = self._payload.encode(payload_encoding) + b"\x00\x00"

        data = identifier_part + message_part
        packet_len = struct.pack("<i", len(data))

        return packet_len + data


class LoginPacket(OutgoingRconPacket):
    """Request packet sent after establishing connection with server."""
    def __init__(self, rcon_password: str, request_id: int):
        self._rcon_password = rcon_password
        self._rid = request_id

    @property
    def _type(self) -> int:
        return 3

    @property
    def _request_id(self) -> int:
        return self._rid

    @property
    def _payload(self) -> str:
        return self._rcon_password


class CommandPacket(OutgoingRconPacket):
    """Request packet containing a single command to execute."""
    def __init__(self, command: str, request_id: int):
        self._command = command
        self._rid = request_id

    @property
    def _payload(self) -> str:
        return self._command

    @property
    def _type(self) -> int:
        return 2

    @property
    def _request_id(self) -> int:
        return self._rid


class CommandEndPacket(OutgoingRconPacket):
    """Correlation packet sent after each command."""
    def __init__(self, request_id: int):
        self._rid = request_id

    @property
    def _payload(self) -> str:
        return ""

    @property
    def _type(self) -> int:
        return 99

    @property
    def _request_id(self) -> int:
        return self._rid


@dataclass(frozen=True, eq=True)
class LoginSuccessResponse:
    """Server response to login packet - success."""
    request_id: int


@dataclass(frozen=True, eq=True)
class InvalidPasswordResponse:
    """Server response to login packet with invalid password."""


@dataclass(frozen=True, eq=True)
class CommandResponse:
    """Response to command packet."""
    request_id: int
    payload: bytes


@dataclass(frozen=True, eq=True)
class UnprocessableResponse:
    """Response packet could not be processed."""
    request_id: int
    message: str


RconResponsePacket = (
        LoginSuccessResponse
        | InvalidPasswordResponse
        | CommandResponse
        | UnprocessableResponse
)


def encoding(game: Server.Type):
    """Selects correct encoding for given game type."""
    match game:
        case Server.Type.SOURCE_SERVER: return "ascii"
        case Server.Type.MINECRAFT_SERVER: return "utf-8"


def _decode_command_response(request_id: int, payload: bytes):
    return CommandResponse(request_id, payload)


def _decode_login_response(request_id: int, _: bytes):
    if request_id == -1:
        return InvalidPasswordResponse()
    return LoginSuccessResponse(request_id)


decoders: dict[int, Callable[[int, bytes], RconResponsePacket]] = {
    0: _decode_command_response,
    2: _decode_login_response
}


async def next_packet(
        read_n: Callable[[int], Awaitable[bytes]],
):
    """
    Reads next packet.

    :param read_n: Function that reads next n bytes
    :return:
    """
    len_bytes = await read_n(4)
    (data_length,) = struct.unpack("<i", len_bytes)
    data_bytes = await read_n(data_length)
    req_id, res_type = struct.unpack("<ii", data_bytes[0:8])
    payload = data_bytes[8:-2]
    padding = data_bytes[-2:]

    return _decode(res_type, req_id, payload, padding)


def _decode(
        packet_type: int,
        request_id: int,
        payload: bytes,
        padding: bytes
) -> RconResponsePacket:
    if padding != b"\x00\x00":
        return UnprocessableResponse(request_id, "Padding mismatch")
    if packet_type not in decoders:
        return UnprocessableResponse(request_id, "Invalid packet type")
    return decoders[packet_type](request_id, payload)
