"""This module contains functions for hashing passwords and verifying hashed passwords."""
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if the plain_password matches the hashed_password.

    :param plain_password:
    :param hashed_password:
    :return: boolean indicating if the plain_password matches the hashed password
    """
    return _pwd_context.verify(plain_password, hashed_password)


def hash_password(plain_password: str) -> str:
    """
    Hashes the plain_password.

    :param plain_password: plaintext password
    :return: hashed password
    """
    return _pwd_context.hash(plain_password)
