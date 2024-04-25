"""This module contains app configuration models."""
from enum import Enum
from typing import Literal, Union

from pydantic import Field
from pydantic.dataclasses import dataclass
from pydantic_settings import BaseSettings


class DatabaseProvider(Enum):
    """Enumeration of database providers."""
    IN_MEMORY = "IN_MEMORY"
    SQLITE = "SQLITE"


@dataclass
class SqliteDbConfiguration:
    """Configuration of SQLite database."""
    db_name: str = "pycon.sqlite3"
    db_provider: Literal[DatabaseProvider.SQLITE] = DatabaseProvider.SQLITE


@dataclass
class InMemoryDbConfiguration:
    """Configuration of in-memory database."""
    db_provider: Literal[DatabaseProvider.IN_MEMORY] = DatabaseProvider.IN_MEMORY


class Configuration(BaseSettings):
    """Application configuration model."""
    db_configuration: Union[SqliteDbConfiguration, InMemoryDbConfiguration] = Field(
        SqliteDbConfiguration(),
        discriminator='db_provider'
    )
    access_token_expire_minutes: int = 120
    access_token_secret: str = "<<replace-me>>"
    base_template_name: str = "base.html"
    default_user_name: str = "admin"
    default_user_password: str = "admin"
