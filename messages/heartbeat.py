from dataclasses import dataclass
from datetime import datetime
from typing import Never, Any, Callable

from jinja2 import Template

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class HeartbeatMessage:
    timestamp: datetime


heartbeat_topic = TopicDescriptor[HeartbeatMessage]("heartbeat")


class HeartbeatConverter(HtmxConverter[Never, HeartbeatMessage, Any]):
    def __init__(self, template_provider: Callable[[str], Template]):
        self._template = template_provider("heartbeat.html")

    def convert_in(self, json: Any) -> Never:
        pass

    def convert_out(self, message: HeartbeatMessage) -> str:
        return self._template.render(timestamp=message.timestamp)
