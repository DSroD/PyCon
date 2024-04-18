import uuid
from dataclasses import dataclass

from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class RconConnected:
    server_uid: uuid.UUID


@dataclass(eq=True, frozen=True)
class RconDisconnected:
    server_uid: uuid.UUID


ServerStatusMessage = RconConnected | RconDisconnected

server_status_topic = TopicDescriptor[ServerStatusMessage]("server_status")
