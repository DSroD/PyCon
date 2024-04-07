import asyncio
from typing import Optional

from starlette.websockets import WebSocket, WebSocketDisconnect

from messages.converter import HtmxConverter
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
    ):
        self._websocket = websocket
        self._converter = converter
        self._pubsub = pubsub
        self._publish_topic = publish_topic
        self._subscribe_topic = subscribe_topic

    async def _read(self):
        async for message in self._websocket.iter_json():
            if not self._publish_topic:
                continue
            converted = self._converter.convert_in(message)
            self._pubsub.publish(self._publish_topic, converted)

    async def _write(self, subscription: Subscription):
        with subscription as sub:
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
        write_task = None
        if self._subscribe_topic:
            subscription = self._pubsub.subscribe(self._subscribe_topic)
            write_task = asyncio.create_task(self._write(subscription))
        try:
            await self._read()
        except asyncio.CancelledError:
            await self._websocket.close()
            raise
        except WebSocketDisconnect:
            raise
        finally:
            if write_task:
                write_task.cancel()
