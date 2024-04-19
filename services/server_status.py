import uuid
from collections import defaultdict
from dataclasses import dataclass

from messages.server_status import server_status_topic, ServerStatusMessage, RconConnected, RconDisconnected
from pubsub.pubsub import PubSub
from services.service import Service


@dataclass
class ServerStatus:
    rcon_connected: bool


class ServerStatusService(Service):
    def __init__(self, pubsub: PubSub):
        self._pubsub = pubsub
        self._server_states = defaultdict(
            lambda: ServerStatus(
                rcon_connected=False
            )
        )

    @property
    def name(self) -> str:
        return "server_state_service"

    async def launch(self):
        with self._pubsub.subscribe(
            server_status_topic
        ) as sub:
            async for msg in sub:
                self._process_msg(msg)

    async def stop(self):
        pass

    def get_state(self, server_id: uuid.UUID):
        return self._server_states[server_id]

    def get_states(self, server_ids: set[uuid.UUID]):
        return {sid: self._server_states[sid] for sid in server_ids}

    def _process_msg(self, msg: ServerStatusMessage):
        match msg:
            case RconConnected(uid):
                self._server_states[uid].rcon_connected = True
            case RconDisconnected(uid):
                self._server_states[uid].rcon_connected = False
