"""User models and views."""
from typing import Union

from pydantic import BaseModel


class UserView(BaseModel):
    """User view - model without sensitive data."""
    username: str


class User(UserView):
    """User model."""
    hashed_password: str
    disabled: Union[bool, None] = None
