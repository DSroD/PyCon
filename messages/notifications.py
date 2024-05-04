"""Notifications to the frontend."""
from dataclasses import dataclass
from enum import Enum
from typing import Never, Any, Optional, Literal, Callable, override

from jinja2 import Template

from messages.converter import HtmxConverter
from pubsub.topic import TopicDescriptor


@dataclass
class NotificationMessage:
    """Message to be shown on the frontend."""
    class NotificationType(Enum):
        """Type of the notification - decides how the notification is displayed."""
        PLAIN = 0
        INFO = 1
        SUCCESS = 2
        WARNING = 3
        ERROR = 4

    audience: list[str] | Literal["all"]
    message: str
    type: NotificationType = NotificationType.PLAIN
    remove_after: Optional[int] = None


notification_topic = TopicDescriptor[NotificationMessage]("notifications")


cls_conversions = {
    NotificationMessage.NotificationType.PLAIN: "plain",
    NotificationMessage.NotificationType.INFO: "info",
    NotificationMessage.NotificationType.SUCCESS: "ok",
    NotificationMessage.NotificationType.WARNING: "warn",
    NotificationMessage.NotificationType.ERROR: "bad",
}


class NotificationConverter(HtmxConverter[Any, Never, NotificationMessage]):
    """Converts NotificationMessages to strings with HTMX components."""
    def __init__(self, template_provider: Callable[[str], Template]):
        self._template = template_provider("notifications/notification.html")

    @override
    def convert_in(self, json: Any) -> Never:
        """Notifications are not received from UI"""

    @override
    def convert_out(self, message: NotificationMessage):
        """Converts NotificationMessage to UI elements to show."""
        cls = cls_conversions.get(message.type, None)
        return self._template.render(
            content=message.message,
            cls=cls,
            remove_after=message.remove_after
        )
