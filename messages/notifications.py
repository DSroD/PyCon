from dataclasses import dataclass
from enum import Enum
from typing import Never, Any, Optional, Literal, Callable

from jinja2 import Template

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass
class NotificationMessage:
    class NotificationType(Enum):
        Plain = 0,
        Info = 1,
        Success = 2,
        Warning = 3,
        Error = 4,

    audience: list[str] | Literal["all"]
    message: str
    type: NotificationType = NotificationType.Plain
    remove_after: Optional[int] = None


notification_topic = TopicDescriptor[NotificationMessage]("notifications")


cls_conversions = {
    NotificationMessage.NotificationType.Plain: "plain",
    NotificationMessage.NotificationType.Info: "info",
    NotificationMessage.NotificationType.Success: "ok",
    NotificationMessage.NotificationType.Warning: "warn",
    NotificationMessage.NotificationType.Error: "bad",
}


class NotificationConverter(HtmxConverter[Any, Never, NotificationMessage]):
    def __init__(self, template_provider: Callable[[str], Template]):
        self._template = template_provider("notifications/notification.html")

    def convert_in(self, json: Any) -> Never:
        pass

    def convert_out(self, message: NotificationMessage):
        cls = cls_conversions.get(message.type, None)
        return self._template.render(
            content=message.message,
            cls=cls,
            remove_after=message.remove_after
        )
