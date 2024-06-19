"""Service that publishes heartbeats."""
import asyncio
from datetime import datetime

from messages.heartbeat import HeartbeatMessage, heartbeat_topic
from pubsub.pubsub import PubSub
from services.service import Service


class HeartbeatPublisherService(Service):
    """Periodically publishes heartbeat messages to the heartbeat topic."""
    @property
    def name(self) -> str:
        return "heartbeat_publisher"

    def __init__(self, pubsub: PubSub, delay: float):
        self._pubsub = pubsub
        self._delay = delay

    async def launch(self):
        while True:
            await asyncio.sleep(self._delay)
            hb = HeartbeatMessage(datetime.now())
            self._pubsub.publish(heartbeat_topic, hb)

    async def stop(self):
        pass
