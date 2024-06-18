"""This module contains app configuration models."""
from enum import Enum
from typing import Literal, Union

from pydantic import Field
from pydantic.dataclasses import dataclass
from pydantic_settings import BaseSettings


# str Enum workaround - https://github.com/pydantic/pydantic/issues/3850#issuecomment-1069353196
class DatabaseProvider(str, Enum):
    """Enumeration of database providers."""
    SQLITE = "SQLITE"


@dataclass
class SqliteDbConfiguration:
    """Configuration of SQLite database."""
    db_name: str = "pycon.sqlite3"
    db_provider: Literal[DatabaseProvider.SQLITE] = DatabaseProvider.SQLITE


class Configuration(BaseSettings):
    """Application configuration model."""
    db_configuration: Union[SqliteDbConfiguration] = Field(
        SqliteDbConfiguration(),
        discriminator='db_provider'
    )
    access_token_expire_minutes: int = 10
    access_token_secret: str = "<<replace-me>>"
    default_user_name: str = "admin"
    default_user_password: str = "admin"
    log_level: str = "INFO"

    class Config:
        """Configuration settings"""
        env_nested_delimiter = '__'
        use_enum_values = True
