from typing import Optional, List

from dao.user_dao import UserDao
from models.user import User, UserInDb


class UserDaoImpl(UserDao):
    def __init__(self):
        self._users = {
            "test": {
                "username": "test",
                # pwd: test
                "hashed_password": "$2b$12$G5zIWm/IHBJwlFxReXNZdu9N7SNCQXe9JKlzSIqWZCzSIFjAlcY.e",
                "disabled": False,
            }
        }

    def initialize(self):
        pass

    def get_all(self) -> List[User]:
        return list(map(lambda user: UserInDb(**user), self._users.values()))

    def get_by_username(self, username: str) -> Optional[User]:
        if username in self._users:
            return User(**self._users[username])
        return None

    def create_user(self, username: str, hashed_password: str) -> Optional[User]:
        if username in self._users:
            return None
        self._users[username] = {
            "username": username,
            "hashed_password": hashed_password,
            "disabled": False
        }

    def delete_user(self, username: str) -> None:
        self._users.pop(username, None)

    def get_with_password(self, username: str) -> Optional[UserInDb]:
        if username in self._users:
            return UserInDb(**self._users[username])
        return None

    def set_disabled(self, username: str, disabled: bool) -> None:
        if username in self._users:
            self._users[username]["disabled"] = disabled
