"""Coverts between PubSub messages and HTMX data."""
from abc import ABC, abstractmethod


class HtmxConverter[DataInT, MessageInT, MessageOutT](ABC):
    """Interface for classes converting WebSocket data."""
    @abstractmethod
    def convert_out(self, message: MessageOutT) -> str:
        """
        Converts outgoing message to HTMX component (as string).

        :param message:
        :return: HTMX component
        """

    @abstractmethod
    def convert_in(self, data: DataInT) -> MessageInT:
        """
        Converts incoming data to a message.

        :param data:
        :return:
        """
