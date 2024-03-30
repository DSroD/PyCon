from datetime import timedelta, datetime, timezone
from typing import Optional

from jose import jwt, JWTError

from models.user import User


class JwtTokenUtils:
    def __init__(self, secret_key: str, access_token_expiry: timedelta):
        self._secret_key = secret_key
        self._access_token_expiry = access_token_expiry

    def create_access_token(
            self,
            user: User,
    ) -> str:
        data_to_encode = {
            'sub': user.username,
            'exp': datetime.now(timezone.utc) + self._access_token_expiry
        }
        encoded = jwt.encode(data_to_encode, self._secret_key, algorithm='HS512')
        return encoded

    def get_user(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=['HS512'])
            username = payload.get('sub', None)
            return username
        except JWTError:
            return None
