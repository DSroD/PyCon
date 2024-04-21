"""Application dependencies."""
import uuid
from typing import Annotated, Optional, TypeVar, Callable

from fastapi import Depends, Cookie

from auth.jwt import JwtTokenUtils
from configuration import Configuration, InMemoryDbConfiguration, SqliteDbConfiguration
from dao.dao import ServerDao, UserDao
from dao.in_memory import (
    UserDaoImpl as InMemoryUserDao,
    ServerDaoImpl as InMemoryServerDao,
)
from dao.sqlite import (
    UserDaoImpl as SqliteUserDao,
    ServerDaoImpl as SqliteServerDao,
)
from messages.rcon import RconWSConverter
from messages.server_status import ServerStatusUpdateConverter
from templating import TemplateProvider

DependencyT = TypeVar("DependencyT")


class Dependencies:
    """Container for dependencies."""
    def __init__(self):
        self._services: dict[type[DependencyT], DependencyT] = {}

    def register(self, dependency: DependencyT, register_type: Optional[type[DependencyT]] = None):
        """
        Registers a dependency.
        :param dependency: Dependency to be registered
        :param register_type: Type to register the dependency as
        """
        service_type = register_type if register_type else type(dependency)
        self._services[service_type] = dependency

    def get(self, service_type: type[DependencyT]) -> Callable[[], DependencyT]:
        """
        Returns a dependency by its type.
        :param service_type: Type of the dependency to retrieve.
        :return: Dependency of given type.
        """
        return lambda: self._services[service_type]


def get_daos(config: Configuration) -> tuple[UserDao, ServerDao]:
    """Initializes data access objects"""
    match config.db_configuration:
        case InMemoryDbConfiguration():
            return (
                InMemoryUserDao(),
                InMemoryServerDao()
            )
        case SqliteDbConfiguration(db_name):
            return (
                SqliteUserDao(db_name),
                SqliteServerDao(db_name)
            )


ioc = Dependencies()


def get_current_user(
        jwt_utils: Annotated[JwtTokenUtils, Depends(ioc.get(JwtTokenUtils))],
        token: Annotated[Optional[str], Cookie()] = None,
):
    """Returns current user if authenticated, otherwise returns None."""
    if token:
        return jwt_utils.get_user(token)
    return None


def rcon_converter_factory(
        templates: Annotated[TemplateProvider, Depends(ioc.get(TemplateProvider))],
        user: Annotated[Optional[str], Depends(get_current_user)],
):
    """Returns a factory for RconWSConverter for given server."""
    def create(
            server_id: uuid.UUID,
    ):
        return RconWSConverter(server_id, user, templates.get_template)
    return create


def status_update_converter_factory(
        templates: Annotated[TemplateProvider, Depends(ioc.get(TemplateProvider))],
):
    """Returns a factory for ServerStatusUpdateConverter for given server."""
    def create(
            server_id: Optional[uuid.UUID],
    ):
        return ServerStatusUpdateConverter(templates.get_template, server_id,)
    return create
