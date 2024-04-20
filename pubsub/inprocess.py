import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Callable

from pubsub.filter import PubSubFilter
from pubsub.pubsub import PubSub, Subscription
from pubsub.topic import TopicDescriptor


class InProcessPubSub(PubSub):
    """
    InProcess PubSub - allows communication between different modules of the app running in the same process
    """
    @dataclass(eq=True, frozen=True)
    class SubscriptionRecord[TMessage]:
        topic: TopicDescriptor[TMessage]
        subscription: Subscription[TMessage]
        msg_filter: PubSubFilter[TMessage]

    def __init__(self):
        self._subscriptions: dict[TopicDescriptor, set[InProcessPubSub.SubscriptionRecord]] = defaultdict(set)
        self._subscription_record_id_map: dict[uuid.UUID, InProcessPubSub.SubscriptionRecord] = dict()

    def publish[TMessage](
            self,
            topic: TopicDescriptor[TMessage],
            message: TMessage
    ):
        subscriptions = self._subscriptions[topic]
        for sub in subscriptions:
            if not sub.msg_filter or sub.msg_filter.accept(message):
                sub.subscription._on_message(message)

    def subscribe[TMessage](
            self,
            topic: TopicDescriptor[TMessage],
            msg_filter: Optional[PubSubFilter] = None,
    ) -> Subscription[TMessage]:
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
