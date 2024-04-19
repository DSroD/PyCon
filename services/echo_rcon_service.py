import uuid

from messages.rcon import rcon_command_topic, RconResponse, rcon_response_topic
from pubsub.filter import FieldLength
from pubsub.pubsub import PubSub
from services.service import Service


class EchoProcessor(Service):
    def __init__(self, pubsub: PubSub, server_id: uuid.UUID):
        self._pubsub = pubsub
        self._server_id = server_id

    @property
    def name(self) -> str:
        return f"echo_processor_{self._server_id}"

    async def launch(self):
        with self._pubsub.subscribe(
            rcon_command_topic(self._server_id),
            FieldLength(lambda msg: msg.command, 64, FieldLength.Mode.MAX) &
            FieldLength(lambda msg: msg.command, 1, FieldLength.Mode.MIN)
        ) as subscription:
            async for message in subscription:
                published = RconResponse(
                    message.issuing_user,
                    message.command,
                    f"ack: {message.command}",
                )
                self._pubsub.publish(rcon_response_topic(self._server_id), published)

    async def stop(self):
        pass
