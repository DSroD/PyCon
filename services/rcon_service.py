import asyncio

from messages.notifications import notification_topic, NotificationMessage
from messages.rcon import rcon_command_topic, rcon_response_topic
from messages.server_status import server_status_topic, RconConnected, RconDisconnected
from models.server import Server
from pubsub.filter import FieldLength
from pubsub.pubsub import PubSub
from rcon.rcon_client import RconClientManager, RconClient
from rcon.request_id import RequestIdProvider
from services.service import Service, RecoverableError


class RconService(Service):
    def __init__(
            self,
            pubsub: PubSub,
            server: Server,
    ):
        self._pubsub = pubsub
        # TODO: this should be supplier to allow changes when processor is running
        self._server = server

    @property
    def name(self) -> str:
        return f"rcon_service_{self._server.uid}"

    async def launch(self):
        try:
            async with RconClientManager(
                RequestIdProvider(),
                self._server.type,
                self._server.host,
                self._server.rcon_port,
                self._server.rcon_password,
                on_failure=self._notify_connection_failure
            ) as client:
                await self._process(client)
        except asyncio.IncompleteReadError as e:
            raise RecoverableError(e, 5000)

    async def _process(self, client):
        self._pubsub.publish(
            server_status_topic,
            RconConnected(self._server.uid)
        )
        self._pubsub.publish(
            notification_topic,
            NotificationMessage(
                audience="all",
                message=f"Connected to RCON of {self._server.name}",
                type=NotificationMessage.NotificationType.Success,
            )
        )

        write_task = asyncio.create_task(self._write(client))
        read_task = asyncio.create_task(self._read(client))
        done, pending = await asyncio.wait(
            [write_task, read_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        self._pubsub.publish(
            server_status_topic,
            RconDisconnected(self._server.uid)
        )
        self._pubsub.publish(
            notification_topic,
            NotificationMessage(
                audience="all",
                message=f"Disconnected from RCON of {self._server.name}",
                type=NotificationMessage.NotificationType.Error,
            )
        )

        for task in pending:
            task.cancel()

    async def _write(self, client: RconClient):
        with self._pubsub.subscribe(
            rcon_command_topic(self._server.uid),
            FieldLength(lambda msg: msg.command, 1, FieldLength.Mode.MIN)
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
        self._pubsub.publish(
            server_status_topic,
            RconDisconnected(self._server.uid)
        )
