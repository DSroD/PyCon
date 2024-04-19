from dataclasses import dataclass
from datetime import datetime
from typing import Never, Callable

from jinja2 import Template

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class HeartbeatMessage:
    timestamp: datetime


heartbeat_topic = TopicDescriptor[HeartbeatMessage]("heartbeat")


class HeartbeatConverter(HtmxConverter[Never, Never, HeartbeatMessage]):
    def __init__(self, template_provider: Callable[[str], Template]):
        self._template = template_provider("heartbeat.html")

    def convert_in(self, data: Never) -> Never:
        pass

    def convert_out(self, message: HeartbeatMessage) -> str:
        return self._template.render(timestamp=message.timestamp)
