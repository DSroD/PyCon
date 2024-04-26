"""SQLite integration tests."""
import sqlite3
# pylint: disable=missing-class-docstring,attribute-defined-outside-init
import unittest
from contextlib import contextmanager
from os import path

import migrator.sqlite
from dao.sqlite import UserDaoImpl, ServerDaoImpl
from models.user import UserCapability


class _UserDaoImpl(UserDaoImpl):
    def __init__(self, db, con):
        super().__init__(db)
        self._con = con

    @contextmanager
    def _conn(self):
        self._con.row_factory = sqlite3.Row
        yield self._con


class _ServerDaoImpl(ServerDaoImpl):
    def __init__(self, db, con):
        super().__init__(db)
        self._con = con

    @contextmanager
    def _conn(self):
        self._con.row_factory = sqlite3.Row
        yield self._con


class SqliteDaoIntegrationTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        db_name = "file::memory:?cache=shared&mode=memory"
        con = sqlite3.connect(db_name, uri=True)
        self.user_dao = _UserDaoImpl(db_name, con)
        self.server_dao = _ServerDaoImpl(db_name, con)
        basepath = path.dirname(__file__)
        filepath = path.abspath(path.join(basepath, "..", "..", "migrations.json"))
        # TODO: fix this
        migrator.sqlite.migrate(con, filepath, False)

    async def test_users_user_create_and_get(self):
        username = "test"
        hashed_pwd = "hashed_pwd"
        capabilities = [UserCapability.USER_MANAGEMENT]

        created = await self.user_dao.create_user(username, hashed_pwd, capabilities)

        user_view_from_db = await self.user_dao.get_view(username)

        user_from_db = await self.user_dao.get(username)

        self.assertEqual(created.username, username)
        self.assertEqual(created.capabilities, capabilities)

        self.assertEqual(user_view_from_db.username, username)
        self.assertEqual(user_view_from_db.capabilities, capabilities)

        self.assertEqual(user_from_db.username, username)
        self.assertEqual(user_from_db.hashed_password, hashed_pwd)
        self.assertEqual(user_from_db.capabilities, capabilities)
        self.assertEqual(user_from_db.disabled, False)

    async def test_users_get_all_usernames(self):
        usernames = ["test1", "test2", "test3"]
        for username in usernames:
            await self.user_dao.create_user(username, "pwd", [])

        users = await self.user_dao.get_all_usernames()
        self.assertEqual(users, usernames)

    async def _test_servers_create_and_get(self):
        pass
