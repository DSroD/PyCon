from abc import ABC, abstractmethod


class Dao(ABC):
    @abstractmethod
    def initialize(self):
        pass
