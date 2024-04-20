from __future__ import annotations

import asyncio
from asyncio import StreamReader, StreamWriter
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Optional, Coroutine

from messages.rcon import RconCommand, RconResponse
from models.server import Server
from rcon.encoding import encoding
from rcon.packets import RconResponsePacket, LoginPacket, OutgoingRconPacket, LoginSuccessResponse, \
    LoginFailedResponse, UnprocessableResponse, CommandPacket, CommandEndPacket, CommandResponse, next_packet
from rcon.rcon_client_errors import RequestIdMismatchError, InvalidPasswordError, InvalidPacketError
from rcon.request_id import RequestIdProvider
from utils.retry import retry_jitter_exponential_backoff as retry


class RconConnection:
    """Connection proxy to the RCON server"""
    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter,
            payload_encoding: str,
    ):
        self._reader = reader
        self._writer = writer
        self._payload_encoding = payload_encoding

    async def write(self, data: OutgoingRconPacket) -> None:
        self._writer.write(data.encode(self._payload_encoding))
        await self._writer.drain()

    async def read(self) -> RconResponsePacket:
        return await next_packet(
            lambda n: self._reader.readexactly(n),
        )

    def close(self):
        self._writer.close()
        self._reader.feed_eof()


class RconClient:
    @dataclass
    class RequestMetadata:
        request_id: int
        issuing_user: str
        command: str

    def __init__(
            self,
            connection: RconConnection,
            request_id_provider: RequestIdProvider,
            payload_encoding: str,
    ):
        self._connection = connection
        self._request_id_provider = request_id_provider
        self._payload_encoding = payload_encoding
        self._responses: dict[int, list[bytes]] = defaultdict(list)
        self._requests: dict[int, RconClient.RequestMetadata] = dict()

    async def send_command(self, msg: RconCommand):
        cmd_id = self._request_id_provider.get_request_id()
        end_id = self._request_id_provider.get_request_id()
        self._requests[end_id] = RconClient.RequestMetadata(
            cmd_id, msg.issuing_user, msg.command
        )
        await self._connection.write(
            CommandPacket(
                msg.command,
                cmd_id
            )
        )
        await self._connection.write(
            CommandEndPacket(
                end_id
            )
        )

    async def read(
            self,
            on_response: Callable[[RconResponsePacket], None],
            on_error: Callable[[str], None] | None = None,
    ):
        while True:
            packet = await self._connection.read()
            match packet:
                case CommandResponse(request_id, payload):
                    if request_id in self._requests:
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
    """Client used to communicate with the RCON server"""
    def __init__(
            self,
            request_id_provider: RequestIdProvider,
            game: Server.Type,
            host: str,
            rcon_port: int,
            rcon_password: str,
            timeout: int = 5,
            on_failure: Optional[Callable[[], Coroutine]] = None,
    ):
        self._request_id_provider = request_id_provider
        self._host = host
        self._rcon_port = rcon_port
        self._rcon_password = rcon_password
        self._timeout = timeout
        self.responses = defaultdict(set)
        self._encoding = encoding(game)
        self._on_failure = on_failure

    async def __aenter__(self) -> RconClient:
        print(f"Connecting to {self._host}:{self._rcon_port}")
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
            backoff_ms=1000,
            jitter_ms=100,
            max_backoff_ms=240000,
            on_failure=self._on_failure
        )

        return RconClient(self._connection, self._request_id_provider, self._encoding)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._connection.close()

    async def _connect(self):
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self._host, self._rcon_port),
            self._timeout
        )

        conn = RconConnection(reader, writer, self._encoding)

        request_id = self._request_id_provider.get_request_id()
        login_packet = LoginPacket(
            self._rcon_password,
            request_id
        )

        await conn.write(login_packet)
        login_response = await conn.read()
        match login_response:
            case LoginSuccessResponse(resp_req_id):
                if resp_req_id != request_id:
                    raise RequestIdMismatchError(request_id, resp_req_id)
            case LoginFailedResponse():
                raise InvalidPasswordError()
            case UnprocessableResponse(request_id, message):
                raise InvalidPacketError(f"{request_id}: {message}")
            case _:
                raise InvalidPacketError("Expected login response.")

        self._connection = conn
