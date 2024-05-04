"""PubSub topics."""
from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class TopicDescriptor[MessageT]:
    """Wrapper class for PubSub topics."""
    topic: str
