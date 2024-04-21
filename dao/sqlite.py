"""SQLite backed implementation of DAOs."""

import sqlite3
import uuid
from typing import Optional, List, override

from dao.dao import ServerDao, UserDao
from models.server import Server
from models.user import UserView, User


class ServerDaoImpl(ServerDao):
    """SQLite implementation of Server Dao."""
    def __init__(self, db_name):
        self._table_name = 'servers'
        self._db_name = db_name

    @override
    async def initialize(self):
        pass

    def _conn(self):
        return sqlite3.connect(self._db_name)

    @override
    async def get_all(self) -> List[Server]:
        pass

    @override
    async def get_user_servers(self, username: str) -> List[Server]:
        pass

    @override
    async def get_by_uid(self, uid: uuid.UUID) -> Optional[Server]:
        pass


class UserDaoImpl(UserDao):
    """SQLite implementation of UserDao."""
    def __init__(self, db_name):
        self._table_name = 'users'
        self._db_name = db_name

    @override
    async def initialize(self):
        pass

    def _conn(self):
        return sqlite3.connect(self._db_name)

    @override
    async def get_all(self) -> List[UserView]:
        pass

    @override
    async def get_by_username(self, username: str) -> Optional[UserView]:
        with self._conn() as _:
            pass

    @override
    async def create_user(self, username: str, hashed_password: str) -> Optional[UserView]:
        pass

    @override
    async def delete_user(self, username: str) -> None:
        pass

    @override
    async def get_with_password(self, username: str) -> Optional[User]:
        pass

    @override
    async def set_disabled(self, username: str, disabled: bool) -> None:
        pass
