import struct
from abc import ABC, abstractmethod


class OutgoingPacket(ABC):
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
    def _message(self) -> str:
        """
        According to wiki.vg, for minecraft servers there might be maximal packet length of 1446
        TODO: investigate
        """
        pass

    def encode(self) -> bytes:
        identifier_part = struct.pack("<ii", self._request_id, self._type)
        # Encoded message (null terminated) and padding byte
        message_part = self._message.encode("utf8") + b"\x00\x00"

        data = identifier_part + message_part
        packet_len = struct.pack("<i", len(data))

        return packet_len + data


class LoginPacket(OutgoingPacket):
    def __init__(self, rcon_password: str):
        pass

    @property
    def _type(self) -> int:
        return 3

    @property
    def _request_id(self) -> int:
        pass


    @property
    def _message(self) -> str:
        pass