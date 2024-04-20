from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class TopicDescriptor[MessageT]:
    topic: str
