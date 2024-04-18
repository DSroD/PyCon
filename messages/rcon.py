import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from jinja2 import Template

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class RconCommand:
    issuing_user: str
    command: str


def rcon_command_topic(server_uuid: uuid.UUID) -> TopicDescriptor[RconCommand]:
    return TopicDescriptor[RconCommand](f"rcon_command/{server_uuid}")


@dataclass(eq=True, frozen=True)
class RconResponse:
    issuing_user: str
    command: str
    response: str


def rcon_response_topic(server_uuid: uuid.UUID) -> TopicDescriptor[RconResponse]:
    return TopicDescriptor[RconResponse](f"rcon_response/{server_uuid}")


class RconWSConverter(HtmxConverter[RconCommand, RconResponse, dict]):
    def __init__(self, server: uuid.UUID, user: str, template_provider: Callable[[str], Template]):
        self._template = template_provider("rcon/response.html")
        self._server = server
        self._user = user

    def convert_in(self, json: dict) -> RconCommand:
        return RconCommand(
            self._user,
            json["command"]
        )

    def convert_out(self, message: RconResponse) -> str:
        return self._template.render(
            command=message.command,
            response=message.response,
            user=message.issuing_user,
            timestamp=datetime.now().strftime("%H:%M:%S")
        )
