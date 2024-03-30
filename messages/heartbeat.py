from dataclasses import dataclass
from datetime import datetime
from typing import Never, Any

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass(eq=True, frozen=True)
class HeartbeatMessage:
    timestamp: datetime


heartbeat_topic = TopicDescriptor[HeartbeatMessage]("heartbeat")


class HeartbeatConverter(HtmxConverter[Never, HeartbeatMessage, Any]):
    def convert_in(self, json: Any) -> Never:
        pass

    def convert_out(self, message: HeartbeatMessage) -> str:
        return f"Heartbeat: {message.timestamp}"
        # TODO: impl


heartbeat_converter = HeartbeatConverter()
