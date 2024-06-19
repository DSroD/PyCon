"""ServerStatus messages."""
import uuid
from dataclasses import dataclass
from typing import Never, Optional, Callable, override

from jinja2 import Template

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class RconConnected:
    """Message signalling RCON connection was established."""
    server_uid: uuid.UUID


@dataclass(eq=True, frozen=True)
class RconDisconnected:
    """Message signalling RCON connection to the server ended."""
    server_uid: uuid.UUID


ServerStatusMessage = RconConnected | RconDisconnected

server_status_topic = TopicDescriptor[ServerStatusMessage]("server_status")


class ServerStatusUpdateConverter(HtmxConverter[Never, Never, ServerStatusMessage]):
    """ServerStatusConverter converts ServerStatus messages to updated UI elements."""
    def __init__(
            self,
            template_provider: Callable[[str], Template],
            server_uid: Optional[uuid.UUID] = None,
    ):
        """
        Converter from ServerStatus messages to UI elements.

        When server_uid is None, converts to UI elements for server list.
        When server_uid is set, converts to UI elements for given server detail
        :param server_uid:
        """
        template = "servers/detail_update.html" if server_uid else "servers/list_update.html"
        self._template = template_provider(template)

    @override
    def convert_in(self, data: Never) -> Never:
        """ServerStatus messages are not received from UI."""

    @override
    def convert_out(self, message: ServerStatusMessage) -> str:
        """Converts ServerStatus messages to HTMX UI update."""
        match message:
            case RconConnected():
                return self._template.render(
                    server_uid=message.server_uid,
                    rcon_connected=True,
                )
            case RconDisconnected():
                return self._template.render(
                    server_uid=message.server_uid,
                    rcon_connected=False,
                )
