from dataclasses import dataclass


@dataclass(eq=True, frozen=True)
class TopicDescriptor[TMessage]:
    topic: str
