"""This module contains data access object interfaces."""
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from models.server import Server
from models.user import UserView, User, UserCapability


class ServerDao(ABC):
    """Data access object for servers."""
    @abstractmethod
    async def get_all(self) -> list[Server]:
        """
        Gets all the persisted servers.

        :return: Servers from the persistence provider.
        """

    @abstractmethod
    async def get_user_servers(self, username: str) -> list[Server]:
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

    @abstractmethod
    async def upsert(self, server: Server, acting_user: Optional[str]) -> Server:
        """Upsert a server."""

    @abstractmethod
    async def set_assigned_users(
            self,
            server_uid: uuid.UUID,
            users: list[str],
            acting_user: Optional[str]
    ) -> None:
        """Sets users assigned to a server."""

    @abstractmethod
    async def get_assigned_usernames(self, server_uid: uuid.UUID) -> list[str]:
        """Gets usernames of users assigned to a server."""

    @abstractmethod
    async def delete(self, uid: uuid.UUID, acting_user: Optional[str]) -> None:
        """Deletes a server from database."""


class UserDao(ABC):
    """Data access object for user data."""
    @abstractmethod
    async def get_all_usernames(self) -> list[str]:
        """
        Returns list of all users.

        :return: List of users.
        """
    @abstractmethod
    async def get_view(self, username: str) -> Optional[UserView]:
        """
        Returns user by username.

        :param username:
        """

    @abstractmethod
    async def create_user(
            self,
            username: str,
            hashed_password: str,
            capabilities: list[UserCapability],
            acting_user: Optional[str],
    ) -> Optional[UserView]:
        """
        Creates new user (if no other with same username exists).

        :param username: Username
        :param hashed_password: Password hash
        :param capabilities: List of user capabilities.
        :param acting_user: Name of the user performing this operation.
        """

    @abstractmethod
    async def delete_user(self, username: str, acting_user: Optional[str]) -> None:
        """
        Removes user by username (if exists).

        :param username: Username
        :param acting_user: Name of the user performing this operation.
        """

    @abstractmethod
    async def get(self, username: str) -> Optional[User]:
        """
        Gets hashed password of a user (if exists).

        :param username: Username
        :return: User if exists, None otherwise.
        """

    @abstractmethod
    async def set_disabled(
            self,
            username: str,
            disabled: bool,
            acting_user: Optional[str]
    ) -> None:
        """
        Sets disabled flag of a user (if exists).

        :param username: Username
        :param disabled: Value of the disabled flag to set
        :param acting_user: Name of the user performing this operation.
        """

    @abstractmethod
    async def get_capabilities(self, username: str) -> list[UserCapability]:
        """
        Gets capabilities of a user.
        :param username:  Username
        :return: List of user capabilities
        """
