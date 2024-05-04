"""Service for communication with RCON."""
import asyncio
import uuid
from typing import Callable, Awaitable, Optional

from messages.notifications import notification_topic, NotificationMessage
from messages.rcon import rcon_command_topic, rcon_response_topic
from messages.server_status import server_status_topic, RconConnected, RconDisconnected
from models.server import Server
from pubsub.filter import FieldLength
from pubsub.pubsub import PubSub
from rcon.rcon_client import RconClientManager, RconClient
from rcon.request_id import IntRequestIdProvider
from services.service import Service, RecoverableError


def rcon_service_name(uid: uuid.UUID) -> str:
    """
    Returns the name of RCON service with given server UUID
    :param uid: UUID of the server
    :return: Service name
    """
    return f"rcon_service_{uid}"


class RconService(Service):
    """Service responsible for connection to and communication with RCON of a server."""
    def __init__(
            self,
            pubsub: PubSub,
            server_uid: uuid.UUID,
            server_supplier: Callable[[], Awaitable[Optional[Server]]],
    ):
        self._pubsub = pubsub
        self._server_supplier = server_supplier
        self._server_uid = server_uid

    @property
    def name(self) -> str:
        return rcon_service_name(self._server_uid)

    async def launch(self):
        async with RconClientManager(
            IntRequestIdProvider(),
            self._server_supplier,
        ) as client:
            await self._process(client)

    async def _process(self, client):
        self._pubsub.publish(
            server_status_topic,
            RconConnected(self._server_uid)
        )
        self._pubsub.publish(
            notification_topic,
            NotificationMessage(
                audience="all",
                message=f"Connected to RCON of {client.server.name}",
                type=NotificationMessage.NotificationType.SUCCESS,
            )
        )

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._write(client))
                tg.create_task(self._read(client))
        finally:
            self._pubsub.publish(
                server_status_topic,
                RconDisconnected(client.server.uid)
            )
            self._pubsub.publish(
                notification_topic,
                NotificationMessage(
                    audience="all",
                    message=f"Disconnected from RCON of {client.server.name}",
                    type=NotificationMessage.NotificationType.ERROR,
                )
            )

    async def _write(self, client: RconClient):
        with self._pubsub.subscribe(
            rcon_command_topic(self._server_uid),
            FieldLength(lambda msg: msg.command, 1, FieldLength.Mode.MIN)
        ) as sub:
            async for cmd in sub:
                await client.send_command(cmd)

    async def _read(self, client: RconClient):
        try:
            await client.read(
                lambda msg: self._pubsub.publish(
                    rcon_response_topic(self._server_uid),
                    msg
                ),
                lambda err_msg: self._pubsub.publish(
                    notification_topic,
                    NotificationMessage(
                        audience="all",
                        message=err_msg,
                        type=NotificationMessage.NotificationType.ERROR,
                    )
                )
            )
        except* asyncio.IncompleteReadError as e:
            raise RecoverableError(e, 5000) from e

    async def stop(self):
        pass
