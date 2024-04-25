"""SQLite backed implementation of DAOs."""

import sqlite3
import uuid
from typing import Optional, List, override

from dao.dao import ServerDao, UserDao
from models.server import Server
from models.user import UserView, User
from utils.sqlite import model_mapper


class UserDaoImpl(UserDao):
    """SQLite implementation of UserDao."""

    def __init__(self, db_name):
        self._db_name = db_name

    def _conn(self, row_factory=model_mapper(User)):
        con = sqlite3.connect(self._db_name)
        con.row_factory = row_factory
        return con

    @override
    async def initialize(self):
        pass

    @override
    async def get_all(self) -> List[UserView]:
        pass

    @override
    async def get_view(self, username: str) -> Optional[UserView]:
        with self._conn() as con:
            pass

    @override
    async def create_user(self, username: str, hashed_password: str) -> Optional[UserView]:
        with self._conn() as con:
            try:
                con.execute(
                    "INSERT INTO users VALUES (?, ?, 0)", (username, hashed_password)
                )
            except sqlite3.IntegrityError:
                return None

            return UserView(username=username)  # TODO: get from db?

    @override
    async def delete_user(self, username: str) -> None:
        pass

    @override
    async def get(self, username: str) -> Optional[User]:
        with self._conn() as con:
            cur = con.execute(
                "SELECT username, hashed_password, disabled FROM users WHERE username = ?",
                (username,)
            )

            return cur.fetchone()

    @override
    async def set_disabled(self, username: str, disabled: bool) -> None:
        pass


class ServerDaoImpl(ServerDao):
    """SQLite implementation of Server Dao."""

    def __init__(self, db_name):
        self._db_name = db_name

    def _conn(self, row_factory=model_mapper(Server)):
        con = sqlite3.connect(self._db_name)
        con.row_factory = row_factory
        return con

    @override
    async def initialize(self):
        pass

    @override
    async def get_all(self) -> List[Server]:
        with self._conn() as con:
            cur = con.execute(
                """
                SELECT uid, type, name, description, host, port, rcon_port, rcon_password
                FROM servers
                """
            )

            return cur.fetchall()

    @override
    async def get_user_servers(self, username: str) -> List[Server]:
        with self._conn() as con:
            cur = con.execute(
                """
                SELECT ut.uid, type, name, description, host, port, rcon_port, rcon_password
                FROM user_servers ut LEFT JOIN servers s ON ut.uid = s.uid
                WHERE ut.username = ?
                """,
                (username,)
            )

            return cur.fetchall()

    @override
    async def get_by_uid(self, uid: uuid.UUID) -> Optional[Server]:
        pass
