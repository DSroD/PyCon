"""SQLite backed implementation of DAOs."""
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime
from typing import Optional, override

from dao.dao import ServerDao, UserDao
from models.server import Server
from models.user import UserView, User, UserCapability, UserUpsert
from utils.sqlite import model_mapper, enum_mapper


class UserDaoImpl(UserDao):
    """SQLite implementation of UserDao."""

    def __init__(self, db_name):
        self._db_name = db_name
        self.con = None

    def _conn(self):
        con = sqlite3.connect(self._db_name)
        con.row_factory = sqlite3.Row
        return closing(con)

    @override
    async def get_all_usernames(self) -> list[str]:
        with self._conn() as con:
            cur = con.execute("SELECT username FROM users WHERE deleted = 0")

            rows = cur.fetchall()
            return list(map(lambda x: x['username'], rows))

    @override
    async def get_view(self, username: str) -> Optional[UserView]:
        with self._conn() as con:
            user_cur = con.execute(
                "SELECT username FROM users WHERE username = ? AND deleted = 0 AND disabled = 0",
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
            "SELECT capability FROM user_capabilities WHERE username = ? AND deleted = 0",
            (username,)
        )
        cap_rows: list[sqlite3.Row] = cap_cur.fetchall()
        caps = list(map(lambda x: x["capability"], cap_rows))
        return caps

    @override
    async def create_user(
            self,
            username: str,
            hashed_password: str,
            capabilities: list[UserCapability],
            acting_user: Optional[str],
    ) -> Optional[UserView]:
        with self._conn() as con:
            with con:
                action_at = datetime.now().isoformat()
                cur_existing = con.execute(
                    "SELECT count(*) FROM users WHERE username = ? AND deleted = 0",
                    (username,)
                )
                (existing, ) = cur_existing.fetchone()
                if existing != 0:
                    return None

                con.execute(
                    """
                    INSERT INTO users(username, hashed_password, created_at, created_by) 
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        hashed_password = excluded.hashed_password,
                        updated_by = excluded.created_by,
                        updated_at = excluded.created_at,
                        deleted=0
                    WHERE users.deleted=1
                    """,
                    (username, hashed_password, action_at, acting_user)
                )
                caps = list(
                    map(
                        lambda cap: (username, cap.name, action_at, acting_user),
                        capabilities
                    )
                )
                con.executemany(
                    """
                    INSERT INTO user_capabilities(username, capability, created_at, created_by) 
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(username, capability) DO UPDATE SET
                        updated_by = excluded.created_by,
                        updated_by = excluded.created_at,
                        deleted=0
                    WHERE user_capabilities.deleted=1
                    """,
                    caps
                )

            return UserView(username=username, capabilities=capabilities)

    @override
    async def upsert_user(self, upsert: UserUpsert, acting_user: Optional[str]):
        with self._conn() as con:
            with con:
                action_at = datetime.now().isoformat()
                pwd_cur = con.execute(
                    """
                    SELECT hashed_password FROM users 
                    WHERE username = ?
                    AND deleted = 0
                    """,
                    (upsert.username,)
                )

                pwd = pwd_cur.fetchone()

                con.execute(
                    """
                    INSERT INTO users(username, hashed_password, disabled, created_at, created_by)
                    VALUES (?, COALESCE(?, ?), ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        hashed_password = COALESCE(excluded.hashed_password, users.hashed_password),
                        disabled = excluded.disabled,
                        updated_by = excluded.created_by,
                        updated_at = excluded.created_at,
                        deleted = 0
                    """,
                    (upsert.username, upsert.hashed_password, pwd, upsert.disabled, action_at, acting_user)
                )
                caps = list(
                    map(
                        lambda cap: (upsert.username, cap.name, action_at, acting_user),
                        upsert.capabilities
                    )
                )

                con.executemany(
                    """
                    INSERT INTO user_capabilities(username, capability, created_at, created_by) 
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(username, capability) DO UPDATE SET
                        updated_by = excluded.created_by,
                        updated_at = excluded.created_at,
                        deleted=0
                    WHERE user_capabilities.deleted=1
                    """,
                    caps
                )

                con.execute(
                    f"""
                    UPDATE user_capabilities
                    SET 
                        deleted = 1,
                        updated_by = ?,
                        updated_at = ?
                    WHERE username = ?
                    AND capability NOT IN ({",".join(('?',)*len(upsert.capabilities))})
                    """,
                    (acting_user, action_at, upsert.username, *map(lambda x: x.name, upsert.capabilities))
                )

    @override
    async def delete_user(self, username: str, acting_user: Optional[str]) -> None:
        with self._conn() as con:
            with con:
                now = datetime.now().isoformat()
                con.execute(
                    """
                    UPDATE users SET 
                    deleted = 1,
                    updated_at = ?,
                    updated_by = ?
                    WHERE username = ?
                    """,
                    (now, acting_user, username)
                )

    @override
    async def get(self, username: str) -> Optional[User]:
        with self._conn() as con:
            user_cur = con.execute(
                """
                SELECT username, hashed_password, disabled FROM users 
                WHERE username = ? AND deleted = 0
                """,
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
    async def set_disabled(self, username: str, disabled: bool, acting_user: Optional[str]) -> None:
        pass

    @override
    async def get_capabilities(self, username: str) -> list[UserCapability]:
        with self._conn() as con:
            cur = con.execute(
                "SELECT capability FROM user_capabilities WHERE username = ? AND deleted = 0",
            )
            cur.rowfactory = enum_mapper(UserCapability)

            return cur.fetchall()


class ServerDaoImpl(ServerDao):
    """SQLite backed implementation of Server Dao."""


    def __init__(self, db_name):
        self._db_name = db_name

    def _conn(self, row_factory=None):
        con = sqlite3.connect(self._db_name)
        con.row_factory = row_factory if row_factory else sqlite3.Row
        return closing(con)

    @override
    async def get_all(self) -> list[Server]:
        with self._conn() as con:
            cur = con.execute(
                """
                SELECT uid, type, name, description, host, port, rcon_port, rcon_password
                FROM servers
                WHERE deleted = 0
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
                AND s.deleted = 0
                AND ut.deleted = 0
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
                AND deleted = 0
                """,
                (str(uid),)
            )
            cur.row_factory = model_mapper(Server)

            return cur.fetchone()

    @override
    async def upsert(self, server: Server, acting_user: Optional[str]) -> Server:
        with self._conn() as con:
            with con:
                con.execute(
                    """
                    INSERT INTO servers (
                        uid,
                        type,
                        name,
                        description,
                        host,
                        port,
                        rcon_port,
                        rcon_password,
                        created_at,
                        created_by
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (uid) DO UPDATE SET
                        type=excluded.type,
                        name=excluded.name,
                        description=excluded.description,
                        host=excluded.host,
                        port=excluded.port,
                        rcon_port=excluded.rcon_port,
                        rcon_password=excluded.rcon_password,
                        updated_at=excluded.updated_at,
                        updated_by=excluded.updated_by,
                        deleted=0
                    """,
                    (
                        str(server.uid),
                        server.type.value,
                        server.name,
                        server.description,
                        server.host,
                        server.port,
                        server.rcon_port,
                        server.rcon_password,
                        datetime.now().isoformat(),
                        acting_user
                    )
                )

        return server

    @override
    async def set_assigned_users(
            self,
            server_uid: uuid.UUID,
            users: list[str],
            acting_user: Optional[str]
    ):
        with self._conn() as con:
            uid = str(server_uid)
            with con:
                existing_server = con.execute(
                    "SELECT count(*) from servers where uid = ? AND deleted = 0",
                    (uid,)
                )
                (existing,) = existing_server.fetchone()

                if existing == 0:
                    return

                now = datetime.now().isoformat()
                con.executemany(
                    """
                    INSERT INTO user_servers (username, uid, created_at, created_by)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT (username, uid) DO UPDATE SET
                        deleted = 0,
                        updated_at=excluded.created_at,
                        updated_by=excluded.created_by
                    """,
                    [(user, uid, now, acting_user) for user in users]
                )

                con.execute(
                    f"""
                    UPDATE user_servers SET 
                        deleted = 1,
                        updated_at= ?,
                        updated_by = ?
                    WHERE uid = ?
                    AND username NOT IN ({",".join("?" * len(users))})
                    """,
                    (now, acting_user, uid, *users)
                )

    @override
    async def get_assigned_usernames(self, server_uid: uuid.UUID) -> list[str]:
        with self._conn() as con:
            cur = con.execute(
                "SELECT username FROM user_servers WHERE uid = ? AND deleted = 0",
                (str(server_uid),)
            )

            cur.row_factory = lambda _, row: row[0]

            return cur.fetchall()

    @override
    async def delete(self, uid: uuid.UUID, acting_user: Optional[str]) -> None:
        with self._conn() as con:
            with con:
                now = datetime.now().isoformat()
                con.execute(
                    """
                    UPDATE servers SET 
                        deleted = 1,
                        updated_at = ?,
                        updated_by = ?
                    WHERE uid = ?
                    """,
                    (now, acting_user, str(uid))
                )

                con.execute(
                    """
                    UPDATE user_servers SET 
                        deleted = 1,
                        updated_at = ?,
                        updated_by = ?
                    WHERE uid = ?
                    """,
                    (now, acting_user, str(uid))
                )
