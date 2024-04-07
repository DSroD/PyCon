import uuid

from messages.rcon import rcon_command_topic
from models.server import Server
from pubsub.filter import FieldEquals
from pubsub.pubsub import PubSub
from services.service import Service


class SourceRconProcessor(Service):
    def __init__(self, pubsub: PubSub, server_id: uuid.UUID, server: Server):
        self._pubsub = pubsub
        self._server_id = server_id
        self._server = server

    @property
    def name(self) -> str:
        return f"source_rcon_processor_{self._server_id}"

    async def launch(self):
        with self._pubsub.subscribe(
            rcon_command_topic,
            FieldEquals(lambda msg: msg.server_id, self._server_id)
        ) as subscription:
            # create client and pass messages to it
            pass

    async def stop(self):
        pass
