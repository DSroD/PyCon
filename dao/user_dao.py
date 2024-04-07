from abc import ABC, abstractmethod
from typing import Optional, List

from dao.dao import Dao
from models.user import User, UserInDb


class UserDao(Dao, ABC):
    @abstractmethod
    async def get_all(self) -> List[User]:
        """
        Returns list of all users
        :return:
        """
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Returns user by username
        :param username:
        :return:
        """
        pass

    @abstractmethod
    async def create_user(self, username: str, hashed_password: str) -> Optional[User]:
        """
        Creates new user (if no other with same username exists)
        :param username:
        :param hashed_password:
        :return:
        """
        pass

    @abstractmethod
    async def delete_user(self, username: str) -> None:
        """
        Removes user by username (if exists)
        :param username:
        :return:
        """
        pass

    @abstractmethod
    async def get_with_password(self, username: str) -> Optional[UserInDb]:
        """
        Gets hashed password of a user (if exists)
        :param username:
        :return:
        """
        pass

    @abstractmethod
    async def set_disabled(self, username: str, disabled: bool) -> None:
        pass
