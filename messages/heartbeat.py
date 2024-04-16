from dataclasses import dataclass
from datetime import datetime
from typing import Never, Any

from fastapi.templating import Jinja2Templates

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class HeartbeatMessage:
    timestamp: datetime


heartbeat_topic = TopicDescriptor[HeartbeatMessage]("heartbeat")


class HeartbeatConverter(HtmxConverter[Never, HeartbeatMessage, Any]):
    def __init__(self, templates: Jinja2Templates):
        self._template = templates.get_template("heartbeat.html")

    def convert_in(self, json: Any) -> Never:
        pass

    def convert_out(self, message: HeartbeatMessage) -> str:
        return self._template.render(
            timestamp=message.timestamp
        )
