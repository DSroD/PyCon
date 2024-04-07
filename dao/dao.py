from abc import ABC, abstractmethod


class Dao(ABC):
    @abstractmethod
    async def initialize(self):
        pass
