import asyncio
import uuid

from messages.rcon import rcon_command_topic, rcon_response_topic
from models.server import Server
from pubsub.filter import FieldEquals
from pubsub.pubsub import PubSub, Subscription
from rcon.rcon_client import RconClientManager, RconClient
from rcon.request_id import RequestIdProvider
from services.service import Service


class RconProcessor(Service):
    def __init__(
            self,
            pubsub: PubSub,
            server_id: uuid.UUID,
            server: Server,
    ):
        self._pubsub = pubsub
        self._server_id = server_id
        self._server = server

    @property
    def name(self) -> str:
        return f"rcon_processor_{self._server_id}"

    async def launch(self):
        async with RconClientManager(
            RequestIdProvider(),
            self._server.type,
            self._server.host,
            self._server.rcon_port,
            self._server.rcon_password,
        ) as client:

            sub = self._pubsub.subscribe(
                rcon_command_topic(self._server_id),
                FieldEquals(lambda msg: msg.server_id, self._server_id)
            )

            done, pending = await asyncio.wait(
                [self._write(client, sub), self._read(client)],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

    @staticmethod
    async def _write(client: RconClient, subscription: Subscription):
        with subscription as sub:
            async for cmd in sub:
                await client.send_command(cmd)

    async def _read(self, client: RconClient):
        await client.read(
            lambda msg: self._pubsub.publish(
                rcon_response_topic(self._server_id),
                msg
            )
        )

    async def stop(self):
        pass
