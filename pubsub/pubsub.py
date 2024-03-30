from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Optional, AsyncIterable, Callable

from aiochannel import Channel

from pubsub.filter import PubSubFilter
from pubsub.topic import TopicDescriptor


class Subscription[TMessage]:
    def __init__(self, pubsub: PubSub, on_exit: Callable[[Subscription], None]):
        self._pubsub = pubsub
        self._on_exit = on_exit
        self._channel: Channel[TMessage] = Channel()

    def _on_message(self, msg: TMessage) -> None:
        self._channel.put_nowait(msg)

    def __enter__(self) -> AsyncIterable[TMessage]:
        return self._channel

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._channel.close()
        self._on_exit(self)


class PubSub(ABC):
    @abstractmethod
    def publish[TMessage](
            self,
            topic: TopicDescriptor[TMessage],
            message: TMessage
    ) -> None:
        pass

    @abstractmethod
    def subscribe[TMessage](
            self,
            topic: TopicDescriptor[TMessage],
            msg_filter: Optional[PubSubFilter] = None
    ) -> Subscription[TMessage]:
        pass
