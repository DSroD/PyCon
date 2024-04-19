from abc import ABC, abstractmethod


class HtmxConverter[TDataIn, TMessageIn, TMessageOut](ABC):
    @abstractmethod
    def convert_out(self, message: TMessageOut) -> str:
        """
        Converts outgoing message to HTMX component
        :param message:
        :return: HTMX component
        """
        pass

    @abstractmethod
    def convert_in(self, data: TDataIn) -> TMessageIn:
        """
        Converts incoming data to a message
        :param data:
        :return:
        """
        pass
