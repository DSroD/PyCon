"""This module provides a class that handles JWT tokens."""
from datetime import timedelta, datetime, timezone, tzinfo
from typing import Optional, Callable

import jwt

from models.user import UserView


class JwtTokenUtils:
    """
    JWT Token Utilities.

    JwtTokenUtils class provides utility functions for JWT tokens - creation of.
    tokens and retrieval of data from JWT tokens.
    """
    def __init__(
            self,
            secret_key: str,
            access_token_expiry: timedelta,
            time_provider: Callable[[tzinfo], datetime] = datetime.now,
    ):
        """
        JwtTokenUtils class provides utility functions for JWT tokens.
        :param secret_key: Key for generating JWT tokens.
        :param access_token_expiry: Expiry time for JWT tokens.
        """
        self._secret_key = secret_key
        self._access_token_expiry = access_token_expiry
        self._time_provider = time_provider

    def create_access_token(self, user: UserView) -> str:
        """
        Creates a JWT access token.

        :param user: User to create JWT access token for.
        :return: JWT access token.
        """
        data_to_encode = {
            "sub": user.username,
            "exp": self._time_provider(timezone.utc) + self._access_token_expiry,
            "scope": list(map(lambda cap: cap.name, user.capabilities)),
        }
        encoded = jwt.encode(data_to_encode, self._secret_key, algorithm='HS512')
        return encoded

    def get_user(self, token: str) -> Optional[UserView]:
        """
        Retrieves a username from JWT token.

        :param token: JWT token.
        :return: Username.
        """
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=['HS512'])
            username = payload.get('sub', None)
            cap_names = payload.get('scope', [])
            caps = list(map(lambda cap: (cap,), cap_names))
            return UserView(
                username=username,
                capabilities=caps,
            )
        except jwt.exceptions.PyJWTError:
            return None
