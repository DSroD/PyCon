import uuid
from dataclasses import dataclass
from datetime import datetime

from starlette.templating import Jinja2Templates

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
    def __init__(self, server: uuid.UUID, user: str, templates: Jinja2Templates):
        self._template = templates.get_template("rcon/response.html")
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
