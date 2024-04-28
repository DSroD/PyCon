"""SQLite integration tests."""
# pylint: disable=missing-class-docstring,attribute-defined-outside-init
import sqlite3
import unittest
from abc import ABC, abstractmethod
from contextlib import contextmanager
from os import path

import migrator.sqlite
from dao.sqlite import UserDaoImpl, ServerDaoImpl
from models.server import Server
from models.user import UserCapability


class PersistenceIntegrationTests(ABC):
    """Base class containing integration tests."""

    async def test_users_user_create_and_get(self):
        """Tests user creation and retrieval."""
        username = "test"
        hashed_pwd = "hashed_pwd"
        capabilities = [UserCapability.USER_MANAGEMENT]

        created = await self._user_dao().create_user(username, hashed_pwd, capabilities, None)

        user_view_from_db = await self._user_dao().get_view(username)

        user_from_db = await self._user_dao().get(username)

        self.assertEqual(created.username, username)
        self.assertEqual(created.capabilities, capabilities)

        self.assertEqual(user_view_from_db.username, username)
        self.assertEqual(user_view_from_db.capabilities, capabilities)

        self.assertEqual(user_from_db.username, username)
        self.assertEqual(user_from_db.hashed_password, hashed_pwd)
        self.assertEqual(user_from_db.capabilities, capabilities)
        self.assertEqual(user_from_db.disabled, False)

    async def test_users_get_all_usernames(self):
        """Tests multiple users creation and retrieval of all usernames."""
        usernames = ["test1", "test2", "test3"]
        for username in usernames:
            await self._user_dao().create_user(username, "pwd", [], None)

        users = await self._user_dao().get_all_usernames()
        self.assertEqual(users, usernames)

    async def test_users_duplicate_create(self):
        """Tests creation of duplicate users."""
        username = "test"
        hashed_pwd1 = "hashed_pwd1"
        hashed_pwd2 = "hashed_pwd2"
        capabilities = []

        _ = await self._user_dao().create_user(username, hashed_pwd1, capabilities, None)
        not_created = await self._user_dao().create_user(username, hashed_pwd2, capabilities, None)

        user = await self._user_dao().get(username)

        self.assertIsNone(not_created)
        self.assertEqual(user.hashed_password, hashed_pwd1)

    async def test_servers_create_and_get(self):
        """Tests server creation and retrieval."""
        server = Server(
            type=Server.Type.MINECRAFT_SERVER,
            name="test server 1",
            description="Description of test server 1",
            host="host.example.com",
            port=25565,
            rcon_port=25575,
            rcon_password="test pwd",
        )

        created = await self._server_dao().upsert(server, None)

        self.assertEqual(created, server)

        fetched = await self._server_dao().get_by_uid(server.uid)

        self.assertEqual(created, fetched)

    async def test_servers_create_and_get_all(self):
        """Tests multiple servers creation and retrieval."""
        names = ["test1", "test2", "test3"]
        servers = [
            Server(
                type=Server.Type.MINECRAFT_SERVER,
                name=name,
                description="test server",
                host="host.example.com",
                port=25565,
                rcon_port=25575,
                rcon_password="test pwd",
            )
            for name in names
        ]

        for server in servers:
            await self._server_dao().upsert(server, None)

        fetched_servers = await self._server_dao().get_all()

        self.assertEqual(servers, fetched_servers)

    async def test_servers_upsert(self):
        """Tests server creation and following update."""
        server = Server(
            type=Server.Type.MINECRAFT_SERVER,
            name="test 1",
            description="test server",
            host="host.example.com",
            port=25565,
            rcon_port=25575,
            rcon_password="test pwd",
        )

        created = await self._server_dao().upsert(server, None)
        self.assertEqual(created, server)

        server.name = "updated name"
        server.description = "updated description"
        await self._server_dao().upsert(server, None)

        fetched = await self._server_dao().get_by_uid(server.uid)
        self.assertEqual(server, fetched)

    @abstractmethod
    def _user_dao(self):
        """Returns User DAO"""

    @abstractmethod
    def _server_dao(self):
        """Returns Server DAO"""

    @abstractmethod
    # pylint: disable-next=invalid-name,missing-function-docstring
    def assertEqual(self, first, second):
        pass

    @abstractmethod
    # pylint: disable-next=invalid-name,missing-function-docstring
    def assertIsNone(self, value):
        pass


class _UserDaoImpl(UserDaoImpl):
    """
    Modified implementation that keeps SQLite connection open
    throughout each test.
    """
    def __init__(self, db, con):
        super().__init__(db)
        self._con = con

    @contextmanager
    def _conn(self):
        self._con.row_factory = sqlite3.Row
        yield self._con


class _ServerDaoImpl(ServerDaoImpl):
    """
        Modified implementation that keeps SQLite connection open
        throughout each test.
        """
    def __init__(self, db, con):
        super().__init__(db)
        self._con = con

    def _conn(self, row_factory=None):
        self._con.row_factory = sqlite3.Row
        return self._con


class SqliteDaoIntegrationTest(unittest.IsolatedAsyncioTestCase, PersistenceIntegrationTests):
    """
    Runner for tests against SQLite.
    """
    def _user_dao(self):
        return self._user_dao_i

    def _server_dao(self):
        return self._server_dao_i

    def setUp(self):
        db_name = ":memory:"
        con = sqlite3.connect(db_name, uri=True)
        self._user_dao_i = _UserDaoImpl(db_name, con)
        self._server_dao_i = _ServerDaoImpl(db_name, con)
        base_path = path.dirname(__file__)
        filepath = path.abspath(path.join(base_path, "..", "..", "migrations.json"))
        migrator.sqlite.migrate(con, filepath, False)
