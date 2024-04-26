"""Client for RCON communication."""
from __future__ import annotations

import asyncio
import logging
from asyncio import StreamReader, StreamWriter
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Optional, Coroutine

from messages.rcon import RconCommand, RconResponse
from models.server import Server
from rcon.packets import (
    RconResponsePacket,
    LoginPacket,
    OutgoingRconPacket,
    LoginSuccessResponse,
    InvalidPasswordResponse,
    UnprocessableResponse,
    CommandPacket,
    CommandEndPacket,
    CommandResponse,
    next_packet, encoding
)
from rcon.rcon_client_errors import RequestIdMismatchError, InvalidPasswordError, InvalidPacketError
from rcon.request_id import IntRequestIdProvider
from utils.retry import retry_jitter_exponential_backoff as retry, RetryConfiguration


logger = logging.getLogger(__name__)


class RconConnection:
    """Connection proxy to the RCON server."""
    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter,
            payload_encoding: str,
    ):
        self._reader = reader
        self._writer = writer
        self._payload_encoding = payload_encoding

    async def send(self, data: OutgoingRconPacket):
        """Sends a packet to the RCON."""
        self._writer.write(data.encode(self._payload_encoding))
        await self._writer.drain()

    async def read(self) -> RconResponsePacket:
        """Reads a single packet from the RCON server."""
        return await next_packet(
            self._reader.readexactly,
        )

    def close(self):
        """Closes the connection."""
        self._writer.close()
        self._reader.feed_eof()


class RconClient:
    """Client for communicating with RCON."""
    @dataclass
    class RequestMetadata:
        """Request metadata."""
        request_id: int
        issuing_user: str
        command: str

    def __init__(
            self,
            connection: RconConnection,
            request_id_provider: IntRequestIdProvider,
            payload_encoding: str,
    ):
        self._connection = connection
        self._request_id_provider = request_id_provider
        self._payload_encoding = payload_encoding
        self._responses: dict[int, list[bytes]] = defaultdict(list)
        self._requests: dict[int, RconClient.RequestMetadata] = {}

    async def send_command(self, msg: RconCommand):
        """Sends a command to the RCON."""
        cmd_id = self._request_id_provider.get_request_id()
        end_id = self._request_id_provider.get_request_id()
        self._requests[end_id] = RconClient.RequestMetadata(
            cmd_id, msg.issuing_user, msg.command
        )
        await self._connection.send(
            CommandPacket(
                msg.command,
                cmd_id
            )
        )
        await self._connection.send(
            CommandEndPacket(
                end_id
            )
        )

    async def read(
            self,
            on_response: Callable[[RconResponsePacket], None],
            on_error: Callable[[str], None] | None = None,
    ):
        """Coroutine that reads responses from RCON."""
        while True:
            packet = await self._connection.read()
            match packet:
                case CommandResponse(request_id, payload):
                    if request_id in self._requests:
                        # Response to end packet received - process responses
                        on_response(self._process_command_response(request_id))
                    else:
                        self._responses[request_id].append(payload)
                case UnprocessableResponse(_, message):
                    if on_error:
                        on_error(message)

                case _:
                    pass

    def _process_command_response(self, ending_id: int) -> RconResponse:
        cmd_metadata = self._requests[ending_id]
        body_parts = self._responses[cmd_metadata.request_id]
        body = b"".join(body_parts)
        response = body.decode(self._payload_encoding)
        return RconResponse(
            issuing_user=cmd_metadata.issuing_user,
            command=cmd_metadata.command,
            response=response
        )


class RconClientManager:
    """Client used to communicate with the RCON server."""
    def __init__(
            self,
            request_id_provider: IntRequestIdProvider,
            server: Server,
            timeout: int = 5,
            on_failure: Optional[Callable[[], Coroutine]] = None,
    ):
        self._request_id_provider = request_id_provider
        self._server = server
        self._timeout = timeout
        self.responses = defaultdict(set)
        self._on_failure = on_failure
        self._connection = None

    async def __aenter__(self) -> RconClient:
        logger.info(
            "Connecting to RCON %s:%s",
            self._server.host,
            self._server.rcon_port,
        )
        await retry(
            self._connect,
            (
                RequestIdMismatchError,
                InvalidPasswordError,
                InvalidPacketError,
                TimeoutError,
                asyncio.TimeoutError,
                ConnectionRefusedError,
                OSError,
            ),
            RetryConfiguration(
                backoff_ms=1000,
                jitter_ms=100,
                max_backoff_ms=240000,
            ),
            on_failure=self._on_failure
        )

        logger.info(
            "Connected to RCON %s:%s",
            self._server.host,
            self._server.rcon_port,
        )

        return RconClient(self._connection, self._request_id_provider, encoding(self._server.type))

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._connection.close()

    async def _connect(self):
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self._server.host, self._server.rcon_port),
            self._timeout
        )

        conn = RconConnection(reader, writer, encoding(self._server.type))

        request_id = self._request_id_provider.get_request_id()
        login_packet = LoginPacket(
            self._server.rcon_password,
            request_id
        )

        await conn.send(login_packet)
        login_response = await conn.read()
        match login_response:
            case LoginSuccessResponse(resp_req_id):
                if resp_req_id != request_id:
                    raise RequestIdMismatchError(request_id, resp_req_id)
            case InvalidPasswordResponse():
                logger.error(
                    "Received invalid password response for RCON %s:%s",
                    self._server.host,
                    self._server.rcon_port,
                )
                raise InvalidPasswordError()
            case UnprocessableResponse(request_id, message):
                logger.warning(
                    "Received unprocessable response for RCON %s:%s",
                    self._server.host,
                    self._server.rcon_port,
                )
                raise InvalidPacketError(f"{request_id}: {message}")
            case _:
                logger.warning(
                    "Received non-login response when expecting login response for RCON %s:%s",
                    self._server.host,
                    self._server.rcon_port,
                )
                raise InvalidPacketError("Expected login response.")

        self._connection = conn
