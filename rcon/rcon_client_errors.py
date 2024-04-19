from typing import Optional


class InvalidPasswordError(Exception):
    pass


class InvalidPacketError(Exception):
    def __init__(self, message: Optional[str] = None):
        self.message = message


class RequestIdMismatchError(Exception):
    def __init__(self, expected: int, received: int):
        self.expected = expected
        self.received = received
