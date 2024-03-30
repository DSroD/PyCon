from typing import Union

from pydantic import BaseModel


class User(BaseModel):
    username: str
    disabled: Union[bool, None] = None


class UserInDb(User):
    hashed_password: str
