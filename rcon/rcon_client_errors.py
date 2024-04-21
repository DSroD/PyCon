"""Errors RCON client can throw."""

from typing import Optional


class InvalidPasswordError(Exception):
    """Login response received signaling invalid password."""


class InvalidPacketError(Exception):
    """Response packet invalid error."""
    def __init__(self, message: Optional[str] = None):
        self.message = message


class RequestIdMismatchError(Exception):
    """Response packet received with unknown request ID."""
    def __init__(self, expected: int, received: int):
        self.expected = expected
        self.received = received
