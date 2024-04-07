from typing import Literal, Union

from pydantic import Field
from pydantic.dataclasses import dataclass
from pydantic_settings import BaseSettings

from dao.database_provider import DatabaseProvider


@dataclass
class SqliteDbConfiguration:
    db_name: str
    db_provider: Literal[DatabaseProvider.SQLITE] = DatabaseProvider.SQLITE


@dataclass
class InMemoryDbConfiguration:
    db_provider: Literal[DatabaseProvider.IN_MEMORY] = DatabaseProvider.IN_MEMORY


class Configuration(BaseSettings):
    db_configuration: Union[SqliteDbConfiguration, InMemoryDbConfiguration] \
        = Field(InMemoryDbConfiguration(), discriminator='db_provider')
    access_token_expire_minutes: int = 30
    access_token_secret: str = "otvDRUIVJkhdVO5oGYGDIMrCpOsBH5OH"
    base_template_name: str = "base.html"
