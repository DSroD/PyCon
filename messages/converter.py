from abc import ABC, abstractmethod


class HtmxConverter[TMessageIn, TMessageOut, TDataIn](ABC):
    @abstractmethod
    def convert_out(self, message: TMessageOut) -> str:
        """
        Converts outgoing message to HTMX component
        :param message:
        :return: HTMX component
        """
        pass

    @abstractmethod
    def convert_in(self, json: TDataIn) -> TMessageIn:
        """
        Converts incoming data to a message
        :param json:
        :return:
        """
        pass
