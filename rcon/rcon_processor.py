import asyncio

from messages.notifications import notification_topic, NotificationMessage
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
            server: Server,
    ):
        self._pubsub = pubsub
        self._server = server

    @property
    def name(self) -> str:
        return f"rcon_processor_{self._server.uid}"

    async def launch(self):
        async with RconClientManager(
            RequestIdProvider(),
            self._server.type,
            self._server.host,
            self._server.rcon_port,
            self._server.rcon_password,
            on_failure=self._notify_connection_failure
        ) as client:
            done, pending = await asyncio.wait(
                [self._write(client), self._read(client)],
                return_when=asyncio.FIRST_COMPLETED
            )

            print("Rcon processor finished.")
            for task in pending:
                task.cancel()

    async def _write(self, client: RconClient):
        with self._pubsub.subscribe(
                rcon_command_topic(self._server.uid),
                FieldEquals(lambda msg: msg.server_id, self._server.uid)
        ) as sub:
            async for cmd in sub:
                await client.send_command(cmd)

    async def _read(self, client: RconClient):
        await client.read(
            lambda msg: self._pubsub.publish(
                rcon_response_topic(self._server.uid),
                msg
            ),
            lambda err_msg: self._pubsub.publish(
                notification_topic,
                NotificationMessage(
                    audience="all",
                    message=err_msg,
                    type=NotificationMessage.NotificationType.Error,
                )
            )
        )

    async def _notify_connection_failure(self):
        self._pubsub.publish(
            notification_topic,
            NotificationMessage(
                audience="all",
                message=f"Failed to connect to {self._server.host}:{self._server.rcon_port}",
                type=NotificationMessage.NotificationType.Warning,
            )
        )

    async def stop(self):
        pass
