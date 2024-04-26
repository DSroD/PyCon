"""User models and views."""
from enum import Enum
from typing import Union

from pydantic import BaseModel


class UserCapability(Enum):
    # Create new users and assign capabilities
    USER_MANAGEMENT = "USER_MANAGEMENT",
    # Create new servers and assign users
    SERVER_MANAGEMENT = "SERVER_MANAGEMENT",


class UserView(BaseModel):
    """User view - model without sensitive data."""
    username: str
    capabilities: list[UserCapability]


class User(UserView):
    """User model."""
    hashed_password: str
    disabled: Union[bool, None] = None
