"""This module contains data access object interfaces."""
import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from models.server import Server
from models.user import UserView, User


class Dao(ABC):  # pylint: disable=too-few-public-methods
    """Base interface for all data access objects."""
    @abstractmethod
    async def initialize(self):
        """
        Initializes the data access object.

        :return:
        """


class ServerDao(Dao, ABC):
    """Data access object for servers."""
    @abstractmethod
    async def get_all(self) -> List[Server]:
        """
        Gets all the persisted servers.

        :return: Servers from the persistence provider.
        """

    @abstractmethod
    async def get_user_servers(self, username: str) -> List[Server]:
        """
        Returns all the servers user can access.

        :param username: User
        :return: List of servers.
        """

    @abstractmethod
    async def get_by_uid(self, uid: uuid.UUID) -> Optional[Server]:
        """
        Get a server by its uuid (if it exists).

        :param uid: Server UUID.
        :return: Server with given UUID
        """


class UserDao(Dao, ABC):
    """Data access object for user data."""
    @abstractmethod
    async def get_all(self) -> List[UserView]:
        """
        Returns list of all users.

        :return: List of users.
        """
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[UserView]:
        """
        Returns user by username.

        :param username:
        :return:
        """

    @abstractmethod
    async def create_user(self, username: str, hashed_password: str) -> Optional[UserView]:
        """
        Creates new user (if no other with same username exists).

        :param username: Username
        :param hashed_password: Password hash
        :return:
        """

    @abstractmethod
    async def delete_user(self, username: str) -> None:
        """
        Removes user by username (if exists).

        :param username: Username
        :return:
        """

    @abstractmethod
    async def get_with_password(self, username: str) -> Optional[User]:
        """
        Gets hashed password of a user (if exists).

        :param username: Username
        :return:
        """

    @abstractmethod
    async def set_disabled(self, username: str, disabled: bool) -> None:
        """
        Sets disabled flag of a user (if exists).

        :param username: Username
        :param disabled: Value of the disabled flag to set
        :return:
        """
