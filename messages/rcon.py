import uuid
from dataclasses import dataclass

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class RconCommand:
    issuing_user: str
    server_id: uuid.UUID
    command: str


rcon_command_topic = TopicDescriptor[RconCommand](f"rcon_command")


@dataclass(eq=True, frozen=True)
class RconResponse:
    issuing_user: str
    server_id: uuid.UUID
    response: str


rcon_response_topic = TopicDescriptor[RconResponse](f"rcon_response")


class RconWSConverter(HtmxConverter[RconCommand, RconResponse, dict]):
    def __init__(self, server: uuid.UUID):
        self._server = server

    def convert_in(self, json: dict) -> RconCommand:
        return RconCommand(
            json["user"],
            self._server,
            json["command"]
        )

    def convert_out(self, message: RconResponse) -> str:
        return f"{message.issuing_user}: {message.response}"
