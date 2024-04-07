from __future__ import annotations


class RconConnection:
    """Connection to the RCON server"""
    pass


class Client:
    """Client used to communicate with the RCON server"""
    def __init__(self, host: str, rcon_port: int, rcon_password: str):
        self._host = host
        self._rcon_port = rcon_port
        self._rcon_password = rcon_password

    async def __aenter__(self) -> Client:
        pass
