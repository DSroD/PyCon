import uuid

from messages.rcon import rcon_command_topic, RconResponse, rcon_response_topic
from pubsub.filter import FieldEquals, FieldLength
from pubsub.pubsub import PubSub
from service.service import Service


class EchoProcessor(Service):
    def __init__(self, pubsub: PubSub, server_id: uuid.UUID):
        self._pubsub = pubsub
        self._server_id = server_id

    def name(self) -> str:
        return f"echo_processor_{self._server_id}"

    async def launch(self):
        with self._pubsub.subscribe(
            rcon_command_topic,
            FieldEquals(lambda msg: msg.server_id, self._server_id) &
            FieldLength(lambda msg: msg.command, 30, 'max')
        ) as subscription:
            async for message in subscription:
                published = RconResponse(
                    message.issuing_user,
                    message.server_id,
                    message.command
                )
                self._pubsub.publish(rcon_response_topic, published)

    async def stop(self):
        pass