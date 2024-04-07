import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from dao.dao import Dao
from models.server import Server


class ServerDao(Dao, ABC):
    @abstractmethod
    async def get_all(self) -> List[Server]:
        """
        Get all the servers
        :return:
        """
        pass

    @abstractmethod
    async def get_user_servers(self, username: str) -> List[Server]:
        """
        Returns all the servers user can access
        :param username:
        :return:
        """
        pass

    @abstractmethod
    async def get_by_uid(self, uid: uuid.UUID) -> Optional[Server]:
        """
        Get a server by its uid (if it exists)
        :param uid:
        :return:
        """
        pass
