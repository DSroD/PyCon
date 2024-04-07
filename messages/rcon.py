import uuid
from dataclasses import dataclass

from starlette.templating import Jinja2Templates

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
    command: str
    response: str


rcon_response_topic = TopicDescriptor[RconResponse](f"rcon_response")


class RconWSConverter(HtmxConverter[RconCommand, RconResponse, dict]):
    def __init__(self, server: uuid.UUID, user: str, templates: Jinja2Templates):
        self._template = templates.get_template("rcon/response.html")
        self._server = server
        self._user = user

    def convert_in(self, json: dict) -> RconCommand:
        return RconCommand(
            self._user,
            self._server,
            json["command"]
        )

    def convert_out(self, message: RconResponse) -> str:
        return self._template.render(
            command=message.command,
            response=message.response,
            user=message.issuing_user,
        )
