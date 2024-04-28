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
        self.con = None

    @contextmanager
    def _conn(self):
        con = sqlite3.connect(self._db_name)
        con.row_factory = sqlite3.Row
        yield con
        con.close()

    @override
    async def get_all_usernames(self) -> list[str]:
        with self._conn() as con:
            cur = con.execute("SELECT username FROM users")

            rows = cur.fetchall()
            return list(map(lambda x: x['username'], rows))

    @override
    async def get_view(self, username: str) -> Optional[UserView]:
        with self._conn() as con:
            user_cur = con.execute(
                "SELECT username FROM users WHERE username = ?",
                (username,)
            )
            user = user_cur.fetchone()
            if not user:
                return None

            caps = await self._get_user_capabilities(con, username)

            return UserView(
                username=user["username"],
                capabilities=caps
            )

    @staticmethod
    async def _get_user_capabilities(con, username):
        cap_cur = con.execute(
            "SELECT capability FROM user_capabilities WHERE username = ?",
            (username,)
        )
        cap_rows: list[sqlite3.Row] = cap_cur.fetchall()
        caps = list(map(lambda x: (x["capability"],), cap_rows))
        return caps

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
            if not user:
                return None

            caps = await self._get_user_capabilities(con, username)

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
    def _conn(self, row_factory=None):
        con = sqlite3.connect(self._db_name)
        con.row_factory = row_factory if row_factory else sqlite3.Row
        yield con
        con.close()

    @override
    async def get_all(self) -> list[Server]:
        with self._conn() as con:
            cur = con.execute(
                """
                SELECT uid, type, name, description, host, port, rcon_port, rcon_password
                FROM servers
                """
            )
            cur.row_factory = model_mapper(Server)

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
            cur.row_factory = model_mapper(Server)

            return cur.fetchall()

    @override
    async def get_by_uid(self, uid: uuid.UUID) -> Optional[Server]:
        with self._conn() as con:
            cur = con.execute(
                """
                SELECT uid, type, name, description, host, port, rcon_port, rcon_password
                FROM servers WHERE uid = ?
                """,
                (str(uid),)
            )
            cur.row_factory = model_mapper(Server)

            return cur.fetchone()

    @override
    async def upsert(self, server: Server) -> Server:
        with self._conn() as con:
            con.execute(
                """
                INSERT INTO servers (uid, type, name, description, host, port, rcon_port, rcon_password)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (uid) DO UPDATE SET
                    type=excluded.type,
                    name=excluded.name,
                    description=excluded.description,
                    host=excluded.host,
                    port=excluded.port,
                    rcon_port=excluded.rcon_port,
                    rcon_password=excluded.rcon_password
                """,
                (
                    str(server.uid),
                    server.type.value,
                    server.name,
                    server.description,
                    server.host,
                    server.port,
                    server.rcon_port,
                    server.rcon_password
                )
            )

        return server
