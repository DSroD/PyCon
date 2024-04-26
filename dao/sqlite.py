"""SQLite backed implementation of DAOs."""

import sqlite3
import uuid
from contextlib import contextmanager
from typing import Optional, override

from dao.dao import ServerDao, UserDao
from models.server import Server
from models.user import UserView, User, UserCapability
from utils.sqlite import model_mapper, enum_mapper


class UserDaoImpl(UserDao):
    """SQLite implementation of UserDao."""

    def __init__(self, db_name):
        self._db_name = db_name

    @contextmanager
    def _conn(self):
        con = sqlite3.connect(self._db_name)
        con.row_factory = sqlite3.Row
        yield con
        con.close()

    @override
    async def initialize(self):
        pass

    @override
    async def get_all(self) -> list[UserView]:
        pass

    @override
    async def get_view(self, username: str) -> Optional[UserView]:
        with self._conn() as con:
            pass

    @override
    async def create_user(
            self,
            username: str,
            hashed_password: str,
            capabilities: list[UserCapability],
    ) -> Optional[UserView]:
        with self._conn() as con:
            with con:
                try:
                    caps = list(map(lambda cap: (username, cap.name), capabilities))
                    con.execute(
                        "INSERT INTO users VALUES (?, ?, 0)", (username, hashed_password)
                    )
                    con.executemany(
                        "INSERT INTO user_capabilities(username, capability) VALUES (?, ?)",
                        caps

                    )
                except sqlite3.IntegrityError:  # TODO: better error handling
                    return None

            return UserView(username=username, capabilities=capabilities)  # TODO: get from db?

    @override
    async def delete_user(self, username: str) -> None:
        pass

    @override
    async def get(self, username: str) -> Optional[User]:
        with self._conn() as con:
            user_cur = con.execute(
                "SELECT username, hashed_password, disabled FROM users WHERE username = ?",
                (username,)
            )
            user = user_cur.fetchone()
            cap_cur = con.execute(
                "SELECT capability FROM user_capabilities WHERE username = ?",
                (username,)
            )
            curs: list[sqlite3.Row] = cap_cur.fetchall()
            caps = list(map(lambda x: (x["capability"],), curs))

            return User(
                username=user["username"],
                hashed_password=user["hashed_password"],
                disabled=user["disabled"],
                capabilities=caps
            )

    @override
    async def set_disabled(self, username: str, disabled: bool) -> None:
        pass

    @override
    async def get_capabilities(self, username: str) -> list[UserCapability]:
        with self._conn() as con:
            cur = con.execute(
                "SELECT capability FROM user_capabilities WHERE username = ?",
            )
            cur.rowfactory = enum_mapper(UserCapability)

            return cur.fetchall()


class ServerDaoImpl(ServerDao):
    """SQLite implementation of Server Dao."""

    def __init__(self, db_name):
        self._db_name = db_name

    @contextmanager
    def _conn(self, row_factory=model_mapper(Server)):
        con = sqlite3.connect(self._db_name)
        con.row_factory = row_factory
        yield con
        con.close()

    @override
    async def initialize(self):
        pass

    @override
    async def get_all(self) -> list[Server]:
        with self._conn() as con:
            cur = con.execute(
                """
                SELECT uid, type, name, description, host, port, rcon_port, rcon_password
                FROM servers
                """
            )

            return cur.fetchall()

    @override
    async def get_user_servers(self, username: str) -> list[Server]:
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
