import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


class RconPacket(ABC):

    @property
    @abstractmethod
    def _type(self) -> int:
        pass

    @property
    @abstractmethod
    def _request_id(self) -> int:
        pass


class OutgoingRconPacket(RconPacket, ABC):
    @property
    @abstractmethod
    def _payload(self) -> str:
        """
        According to wiki.vg, for minecraft servers there might be maximal packet length of 1446
        TODO: investigate
        """
        pass

    def encode(self, payload_encoding: str) -> bytes:
        identifier_part = struct.pack("<ii", self._request_id, self._type)
        # Encoded message (null terminated) and padding byte
        message_part = self._payload.encode(payload_encoding) + b"\x00\x00"

        data = identifier_part + message_part
        packet_len = struct.pack("<i", len(data))

        return packet_len + data


class LoginPacket(OutgoingRconPacket):
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
    def __init__(self, request_id: int):
        self._rid = request_id

    @property
    def _payload(self) -> str:
        return ""

    @property
    def _type(self) -> int:
        return 2

    @property
    def _request_id(self) -> int:
        return self._rid


class LoginSuccessResponse:
    def __init__(self, request_id: int):
        self._rid = request_id

    @property
    def request_id(self):
        return self._rid


class LoginFailedResponse:
    pass


@dataclass
class CommandResponse:
    request_id: int
    payload: bytes


@dataclass
class UnprocessableResponse:
    request_id: int
    message: str


ResponseRconPacket = LoginSuccessResponse | LoginFailedResponse | CommandResponse | UnprocessableResponse


def _decode_command_response(request_id: int, payload: bytes):
    return CommandResponse(request_id, payload)


def _decode_login_response(request_id: int, _: bytes):
    if request_id == -1:
        return LoginFailedResponse()
    return LoginSuccessResponse(request_id)


decoders: dict[int, Callable[[int, bytes], ResponseRconPacket]] = {
    0: _decode_command_response,
    2: _decode_login_response
}


def decode(packet_type: int, request_id: int, payload: bytes, padding: bytes) -> ResponseRconPacket:
    if padding != b"\x00\x00":
        return UnprocessableResponse(request_id, "Padding mismatch")
    if packet_type not in decoders:
        return UnprocessableResponse(request_id, "Invalid packet type")
    return decoders[packet_type](request_id, payload)
