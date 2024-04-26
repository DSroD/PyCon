"""SQLite integration tests."""
# pylint: disable=missing-class-docstring,attribute-defined-outside-init
import unittest
from os import path

import migrator.sqlite
from dao.sqlite import UserDaoImpl, ServerDaoImpl
from models.user import UserCapability


class SqliteDaoIntegrationTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user_dao = UserDaoImpl("file::memory:?cache=shared&mode=memory")
        self.server_dao = ServerDaoImpl("file::memory:?cache=shared&mode=memory")
        basepath = path.dirname(__file__)
        filepath = path.abspath(path.join(basepath, "..", "..", "migrations.json"))
        # TODO: fix this
        migrator.sqlite.migrate("file::memory:?cache=shared&mode=memory", filepath)

    async def _test_user_create_and_get(self):
        username = "test"
        hashed_pwd = "hashed_pwd"
        capabilities = [UserCapability.USER_MANAGEMENT]

        created = await self.user_dao.create_user(username, hashed_pwd, capabilities)

        user_view_from_db = await self.user_dao.get_view(username)

        self.assertIsNotNone(created)
        self.assertIsNotNone(user_view_from_db)


