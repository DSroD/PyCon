"""User models and views."""
from enum import Enum
from typing import Annotated, Optional

from fastapi import Form
from pydantic import BaseModel

from auth.hashing import hash_password


class UserCapability(Enum):
    """Capabilities of users."""
    # Create new users and assign capabilities
    USER_MANAGEMENT = "USER_MANAGEMENT"
    # Create new servers and assign users
    SERVER_MANAGEMENT = "SERVER_MANAGEMENT"


class UserView(BaseModel):
    """User view - model without sensitive data."""
    username: str
    capabilities: list[UserCapability]


class UserUpsert(UserView):
    """Model for user upsert"""
    disabled: bool = False
    hashed_password: Optional[str] = None


class User(UserView):
    """User model."""
    hashed_password: str
    disabled: bool = False


def from_form_data(
        username: Annotated[str, Form()],
        capabilities: Annotated[list[str], Form()] = None,
        password: Annotated[Optional[str], Form()] = None,
        disabled: Annotated[bool, Form()] = False,
) -> UserUpsert:
    """Returns user model from Form data."""
    hashed_pwd = hash_password(password) if password else None
    capabilities = capabilities if capabilities else []
    caps = list(map(lambda x: UserCapability[x], capabilities))
    return UserUpsert(
        username=username,
        hashed_password=hashed_pwd,
        disabled=disabled,
        capabilities=caps
    )
