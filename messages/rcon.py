"""Rcon messages."""
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, override

from jinja2 import Template

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class RconCommand:
    """Rcon command message."""
    issuing_user: str
    command: str


def rcon_command_topic(server_uuid: uuid.UUID) -> TopicDescriptor[RconCommand]:
    """Returns a topic descriptor for a RCON command messages to a given server."""
    return TopicDescriptor[RconCommand](f"rcon_command/{server_uuid}")


@dataclass(eq=True, frozen=True)
class RconResponse:
    """Rcon response message."""
    issuing_user: str
    command: str
    response: str


def rcon_response_topic(server_uuid: uuid.UUID) -> TopicDescriptor[RconResponse]:
    """Returns a topic descriptor for a RCON responses from a given server."""
    return TopicDescriptor[RconResponse](f"rcon_response/{server_uuid}")


class RconWSConverter(HtmxConverter[dict, RconCommand, RconResponse]):
    """Converts RCON messages to/from WS data."""
    def __init__(self, server: uuid.UUID, user: str, template_provider: Callable[[str], Template]):
        self._template = template_provider("rcon/response.html")
        self._server = server
        self._user = user

    @override
    def convert_in(self, data: dict) -> RconCommand:
        """Converts RCON commands from UI to RconCommand messages."""
        return RconCommand(
            self._user,
            data["command"]
        )

    @override
    def convert_out(self, message: RconResponse) -> str:
        """Converts RCON response messages to UI elements to show."""
        return self._template.render(
            command=message.command,
            response=message.response,
            user=message.issuing_user,
            timestamp=datetime.now().strftime("%H:%M:%S")
        )
