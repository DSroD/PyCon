"""PubSub tests."""
# pylint: disable=missing-class-docstring
import asyncio
import unittest
from dataclasses import dataclass

from pubsub.filter import FieldContains, FieldLength, IsType, FieldEquals
from pubsub.inprocess import InProcessPubSub
from pubsub.topic import TopicDescriptor
from utils.async_helpers import yield_to_event_loop


@dataclass(eq=True, frozen=True)
class Message:
    field1: str
    field2: str


@dataclass(eq=True, frozen=True)
class StrListMessage:
    str_content: str
    list_content: list[int]


# TODO: https://github.com/wolever/parameterized
class InProcessPubSubTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.pubsub = InProcessPubSub()
        self.messages_in = []

    async def test_message(self):
        """Tests subscriber receives published messages."""
        topic = TopicDescriptor[int]("int_topic")

        messages_out = [1, 2]

        await self._pubsub_test(topic, messages_out)

        self.assertEqual(messages_out, self.messages_in)

    async def test_filter_field_contains(self):
        """Tests FiledContains filter."""
        topic = TopicDescriptor[StrListMessage]("msg_topic")

        messages_out = [
            StrListMessage(str_content="hello", list_content=[1, 2]),
            StrListMessage(str_content="world", list_content=[1, 2, 3]),
        ]

        msg_filter1 = FieldContains[StrListMessage, str, str](lambda msg: msg.str_content, "ll")

        await self._pubsub_test(topic, messages_out, msg_filter1)
        self.assertEqual([messages_out[0]], self.messages_in)
        self.messages_in.clear()

        msg_filter2 = FieldContains[StrListMessage, int, list](lambda msg: msg.list_content, 3)
        await self._pubsub_test(topic, messages_out, msg_filter2)
        self.assertEqual([messages_out[1]], self.messages_in)

    async def test_filter_field_length(self):
        """Tests FieldLength filter."""
        topic = TopicDescriptor[StrListMessage]("str")

        messages_out = [
            StrListMessage(str_content="h", list_content=[]),
            StrListMessage(str_content="very long string", list_content=[1]),
            StrListMessage(str_content="short string", list_content=[1, 2, 3, 4, 5]),
        ]

        msg_filter1 = FieldLength[StrListMessage, str](
            lambda msg: msg.str_content,
            1,
            FieldLength.Mode.MAX,
        )
        await self._pubsub_test(topic, messages_out, msg_filter1)
        self.assertEqual([messages_out[0]], self.messages_in)
        self.messages_in.clear()

        msg_filter2 = FieldLength[StrListMessage, list](
            lambda msg: msg.list_content,
            1,
            FieldLength.Mode.EQ,
        )
        await self._pubsub_test(topic, messages_out, msg_filter2)
        self.assertEqual([messages_out[1]], self.messages_in)
        self.messages_in.clear()

        msg_filter3 = FieldLength[StrListMessage, list](
            lambda msg: msg.list_content,
            1,
            FieldLength.Mode.MIN,
        )
        await self._pubsub_test(topic, messages_out, msg_filter3)
        self.assertEqual([messages_out[1], messages_out[2]], self.messages_in)

    async def test_filter_is_type(self):
        """Tests IsType filter."""
        @dataclass(eq=True, frozen=True)
        class Msg1:
            pass

        @dataclass(eq=True, frozen=True)
        class Msg2:
            pass

        topic = TopicDescriptor[Msg1 | Msg2]("msg_topic")

        messages_out = [
            Msg1(),
            Msg2(),
            Msg1(),
            Msg2(),
            Msg2()
        ]

        msg_filter1 = IsType[Msg1](Msg1)
        await self._pubsub_test(topic, messages_out, msg_filter1)
        self.assertEqual([messages_out[0], messages_out[2]], self.messages_in)
        self.messages_in.clear()

        msg_filter2 = IsType[Msg2](Msg2)
        await self._pubsub_test(topic, messages_out, msg_filter2)
        self.assertEqual(
            [messages_out[1], messages_out[3], messages_out[4]],
            self.messages_in
        )

    async def test_filter_field_equals(self):
        """Tests FieldEquals filter."""
        topic = TopicDescriptor[Message]("msg_topic")

        messages_out = [
            Message(field1="hello", field2="world"),
            Message(field1="world", field2="hello"),
            Message(field1="hello", field2="another world"),
            Message(field1="another hello", field2="world"),
        ]

        msg_filter1 = FieldEquals[Message, str](lambda msg: msg.field1, "hello")
        await self._pubsub_test(topic, messages_out, msg_filter1)
        self.assertEqual([messages_out[0], messages_out[2]], self.messages_in)
        self.messages_in.clear()

        msg_filter2 = FieldEquals[Message, str](lambda msg: msg.field2, "world")
        await self._pubsub_test(topic, messages_out, msg_filter2)
        self.assertEqual([messages_out[0], messages_out[3]], self.messages_in)

    async def test_filter_or(self):
        """Tests filter or operator."""
        topic = TopicDescriptor[Message]("msg_topic")

        messages_out = [
            Message(field1="hello", field2="world"),
            Message(field1="world", field2="hello"),
            Message(field1="something", field2="else"),
        ]

        msg_filter = (FieldEquals[Message, str](lambda msg: msg.field1, "hello")
                      | FieldEquals[Message, str](lambda msg: msg.field1, "world"))

        await self._pubsub_test(topic, messages_out, msg_filter)
        self.assertEqual([messages_out[0], messages_out[1]], self.messages_in)

    async def test_filter_and(self):
        """Tests filter and operator."""
        topic = TopicDescriptor[Message]("msg_topic")

        messages_out = [
            Message(field1="hello", field2="world"),
            Message(field1="world", field2="hello"),
            Message(field1="hello", field2="different"),
            Message(field1="different", field2="world"),
        ]

        msg_filter = (FieldEquals[Message, str](lambda msg: msg.field1, "hello")
                      & FieldEquals[Message, str](lambda msg: msg.field2, "world"))

        await self._pubsub_test(topic, messages_out, msg_filter)
        self.assertEqual([messages_out[0]], self.messages_in,)

    async def test_filter_not(self):
        """Tests filter not operator."""
        topic = TopicDescriptor[Message]("msg_topic")

        messages_out = [
            Message(field1="hello", field2="world"),
            Message(field1="another", field2="world"),
            Message(field1="different", field2="..."),
            Message(field1="hello", field2="something else"),
        ]

        msg_filter = ~FieldEquals[Message, str](lambda msg: msg.field1, "hello")

        await self._pubsub_test(topic, messages_out, msg_filter)
        self.assertEqual([messages_out[1], messages_out[2]], self.messages_in)

    async def _pubsub_test(
            self,
            topic,
            messages,
            msg_filter=None,
    ):
        async def read():
            with self.pubsub.subscribe(topic, msg_filter) as sub:
                async for msg in sub:
                    self.messages_in.append(msg)

        task = asyncio.create_task(read())
        await yield_to_event_loop()

        for message in messages:
            self.pubsub.publish(topic, message)

        await yield_to_event_loop()

        task.cancel()
