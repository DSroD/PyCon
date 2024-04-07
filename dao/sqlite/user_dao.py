import sqlite3
from typing import Optional

from dao.user_dao import UserDao
from models.user import User, UserInDb


class UserDaoImpl(UserDao):
    def __init__(self, db_name):
        self._table_name = 'users'
        self._db_name = db_name

    async def initialize(self):
        pass

    def _conn(self):
        return sqlite3.connect(self._db_name)

    async def get_by_username(self, username: str) -> Optional[User]:
        with self._conn() as conn:
            pass

    async def create_user(self, username: str, hashed_password: str) -> Optional[User]:
        pass

    async def delete_user(self, username: str) -> None:
        pass

    async def get_with_password(self, username: str) -> Optional[UserInDb]:
        pass

    async def set_disabled(self, username: str, disabled: bool) -> None:
        pass
