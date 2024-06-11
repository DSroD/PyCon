"""
WebSocket Processor sends HTMX components from incoming PubSub messages.

to websockets and publishes incoming websocket messages to PubSub.
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from fastapi.websockets import WebSocket

from messages.converter import HtmxConverter
from pubsub.filter import PubSubFilter
from pubsub.pubsub import PubSub
from pubsub.topic import TopicDescriptor


logger = logging.getLogger(__name__)


@dataclass
class WebsocketPubSub[MessageInT, MessageOutT]:
    """PubSub and topics for websocket processor."""
    pubsub: PubSub
    publish_topic: Optional[TopicDescriptor[MessageInT]]
    subscribe_topic: Optional[TopicDescriptor[MessageOutT]]
    subscribe_filter: Optional[PubSubFilter] = None


class WebsocketProcessor[DataInT, MessageInT, MessageOutT]:
    """
    Processes websocket messages and publishes them to publish topic,.

    subscribes to subscribe_topic with subscribe_filter and publishes
    messages to websocket.
    """
    def __init__(
            self,
            websocket: WebSocket,
            converter: HtmxConverter[DataInT, MessageInT, MessageOutT],
            ws_pubsub: WebsocketPubSub[MessageInT, MessageOutT],
    ):
        self._websocket = websocket
        self._converter = converter
        self._ws_pubsub = ws_pubsub

    async def _read(self):
        """Reads WS and publishes messages to publish_topic."""
        async for message in self._websocket.iter_json():
            if not self._ws_pubsub.publish_topic:
                continue
            converted = self._converter.convert_in(message)
            logger.debug(
                "Publishing message: %s to %s",
                converted,
                self._ws_pubsub.publish_topic.topic,
            )
            self._ws_pubsub.pubsub.publish(
                self._ws_pubsub.publish_topic, converted
            )

    async def _write(self):
        """Writes messages from subscribe_topic to WS."""
        if self._ws_pubsub.subscribe_topic:
            with self._ws_pubsub.pubsub.subscribe(
                    self._ws_pubsub.subscribe_topic,
                    self._ws_pubsub.subscribe_filter
            ) as sub:
                async for msg in sub:
                    converted = self._converter.convert_out(msg)
                    await self._websocket.send_text(converted)

    async def process(self):
        """
        Starts reading the websocket, publishing content to publish_topic.

        and writes messages from subscribe_topic to the websocket
        :return:
        """
        await self._websocket.accept()
        write_task = asyncio.create_task(self._write())
        read_task = asyncio.create_task(self._read())
        try:
            await asyncio.wait(
                [write_task, read_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
        except asyncio.CancelledError:
            await self._websocket.close()
            raise
        finally:
            write_task.cancel()
            read_task.cancel()
