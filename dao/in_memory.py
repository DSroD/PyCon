"""InMemory persistence implementations of DAOs."""

import uuid
from typing import List, Optional, override

from dao.dao import ServerDao, UserDao
from models.server import Server
from models.user import UserView, User


class ServerDaoImpl(ServerDao):
    """InMemory implementation of ServerDao."""
    def __init__(self):
        self._servers = {
            uuid.UUID("141a5347-abfc-4c13-8d10-bba20a261f69"): {
                "type": Server.Type.MINECRAFT_SERVER,
                "name": "Test server",
                "host": "localhost",
                "port": 25565,
                "rcon_port": 25575,
                "rcon_password": "test_server_rcon_pwd1",
                "description": "Test server description",
                "uid": uuid.UUID("141a5347-abfc-4c13-8d10-bba20a261f69"),
                "allowed_users": ["test"]
            },
            uuid.UUID("141a5347-abfc-4c13-8d10-bba20a251f69"): {
                "type": Server.Type.MINECRAFT_SERVER,
                "name": "Test server 2",
                "host": "localhost",
                "port": 25566,
                "rcon_port": 25576,
                "rcon_password": "test_server_rcon_pwd2",
                "description": "Test server 2 description",
                "uid": uuid.UUID("141a5347-abfc-4c13-8d10-bba20a251f69"),
                "allowed_users": ["test", "test2"]
            }
        }

    async def initialize(self):
        pass

    @override
    async def get_user_servers(self, username: str) -> List[Server]:
        return [
            Server(**server) for server
            in self._servers.values()
            if username in server["allowed_users"]
        ]

    @override
    async def get_by_uid(self, uid: uuid.UUID) -> Optional[Server]:
        if uid in self._servers:
            return Server(**self._servers[uid])
        return None

    @override
    async def get_all(self) -> List[Server]:
        return list(map(lambda s: Server(**s), self._servers.values()))


class UserDaoImpl(UserDao):
    """InMemory implementation of UserDao."""
    def __init__(self):
        self._users = {
            "test": {
                "username": "test",
                # pwd: test
                "hashed_password": "$2b$12$G5zIWm/IHBJwlFxReXNZdu9N7SNCQXe9JKlzSIqWZCzSIFjAlcY.e",
                "disabled": False,
            },
            "test2": {
                "username": "test2",
                # pwd: test
                "hashed_password": "$2b$12$G5zIWm/IHBJwlFxReXNZdu9N7SNCQXe9JKlzSIqWZCzSIFjAlcY.e",
                "disabled": False,
            }
        }

    @override
    async def initialize(self):
        pass

    @override
    async def get_all(self) -> List[UserView]:
        return list(map(lambda user: User(**user), self._users.values()))

    @override
    async def get_by_username(self, username: str) -> Optional[UserView]:
        if username in self._users:
            return UserView(**self._users[username])
        return None

    @override
    async def create_user(self, username: str, hashed_password: str) -> Optional[UserView]:
        if username in self._users:
            return None
        self._users[username] = {
            "username": username,
            "hashed_password": hashed_password,
            "disabled": False
        }

    @override
    async def delete_user(self, username: str) -> None:
        self._users.pop(username, None)

    @override
    async def get_with_password(self, username: str) -> Optional[User]:
        if username in self._users:
            return User(**self._users[username])
        return None

    @override
    async def set_disabled(self, username: str, disabled: bool) -> None:
        if username in self._users:
            self._users[username]["disabled"] = disabled
