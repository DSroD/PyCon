"""InProcess messaging using PubSub."""
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Callable, override

from pubsub.filter import PubSubFilter
from pubsub.pubsub import PubSub, Subscription
from pubsub.topic import TopicDescriptor


class InProcessPubSub(PubSub):
    """PubSub messaging between different modules of the app in the same process."""
    @dataclass(eq=True, frozen=True)
    class SubscriptionRecord[MessageT]:
        """Registered subscription."""
        topic: TopicDescriptor[MessageT]
        subscription: Subscription[MessageT]
        msg_filter: PubSubFilter[MessageT]

    def __init__(self):
        self._subscriptions: dict[
            TopicDescriptor,
            set[InProcessPubSub.SubscriptionRecord]
        ] = defaultdict(set)
        self._subscription_record_id_map: dict[uuid.UUID, InProcessPubSub.SubscriptionRecord] = {}

    @override
    def publish[MessageT](
            self,
            topic: TopicDescriptor[MessageT],
            message: MessageT
    ):
        subscriptions = self._subscriptions[topic]
        for sub in subscriptions:
            if not sub.msg_filter or sub.msg_filter.accept(message):
                # pylint: disable=protected-access
                sub.subscription._on_message(message)

    @override
    def subscribe[MessageT](
            self,
            topic: TopicDescriptor[MessageT],
            msg_filter: Optional[PubSubFilter] = None,
    ) -> Subscription[MessageT]:
        sub_id = uuid.uuid4()
        subscription = Subscription(self, self._unsubscribe(sub_id))
        record = InProcessPubSub.SubscriptionRecord(topic, subscription, msg_filter)
        self._subscriptions[topic].add(record)
        self._subscription_record_id_map[sub_id] = record
        return subscription

    def _unsubscribe(self, subscription_id: uuid.UUID) -> Callable[[Subscription], None]:
        def _inner(_: Subscription):
            record = self._subscription_record_id_map.pop(subscription_id)
            self._subscriptions[record.topic].remove(record)
        return _inner
