import asyncio
from typing import Optional

from starlette.websockets import WebSocket, WebSocketDisconnect

from messages.converter import HtmxConverter
from pubsub.filter import PubSubFilter
from pubsub.pubsub import PubSub, Subscription
from pubsub.topic import TopicDescriptor


class Processor[TMessageIn, TMessageOut, TDataIn]:
    def __init__(
            self,
            websocket: WebSocket,
            converter: HtmxConverter[TMessageIn, TMessageOut, TDataIn],
            pubsub: PubSub,
            publish_topic: Optional[TopicDescriptor[TMessageIn]],
            subscribe_topic: Optional[TopicDescriptor[TMessageOut]],
            subscribe_filter: Optional[PubSubFilter] = None,
    ):
        self._websocket = websocket
        self._converter = converter
        self._pubsub = pubsub
        self._publish_topic = publish_topic
        self._subscribe_topic = subscribe_topic
        self._subscribe_filter = subscribe_filter

    async def _read(self):
        async for message in self._websocket.iter_json():
            if not self._publish_topic:
                continue
            converted = self._converter.convert_in(message)
            self._pubsub.publish(self._publish_topic, converted)

    async def _write(self):
        if self._subscribe_topic:
            with self._pubsub.subscribe(self._subscribe_topic, self._subscribe_filter) as sub:
                async for msg in sub:
                    converted = self._converter.convert_out(msg)
                    await self._websocket.send_text(converted)

    async def process(self):
        """
        Starts reading the websocket, publishing content to publish_topic and writes messages from subscribe_topic
        to the websocket
        :return:
        """
        await self._websocket.accept()

        (done, pending) = await asyncio.wait(
            [self._write(), self._read()],
            return_when=asyncio.FIRST_EXCEPTION
        )

        print("ending...")
        for task in pending:
            task.cancel()

