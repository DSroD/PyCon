"""Heartbeat messages."""
from dataclasses import dataclass
from datetime import datetime
from typing import Never, Callable, override

from jinja2 import Template

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class HeartbeatMessage:
    """Heartbeat message containing timestamp of the HB."""
    timestamp: datetime


heartbeat_topic = TopicDescriptor[HeartbeatMessage]("heartbeat")


class HeartbeatConverter(HtmxConverter[Never, Never, HeartbeatMessage]):
    """Converts a heartbeat messages to HTMX components."""
    def __init__(self, template_provider: Callable[[str], Template]):
        self._template = template_provider("heartbeat.html")

    @override
    def convert_in(self, data: Never) -> Never:
        """Heartbeat messages are not received from UI."""

    @override
    def convert_out(self, message: HeartbeatMessage) -> str:
        """Converts heartbeat message to a HTMX component update."""
        return self._template.render(timestamp=message.timestamp)
