"""Application dependencies."""
import uuid
from typing import Annotated, Optional, TypeVar, Callable

from fastapi import Depends, Cookie, HTTPException

import migrator.sqlite
from auth.jwt import JwtTokenUtils
from configuration import Configuration, SqliteDbConfiguration
from dao.dao import ServerDao, UserDao
from dao.sqlite import (
    UserDaoImpl as SqliteUserDao,
    ServerDaoImpl as SqliteServerDao,
)
from messages.rcon import RconWSConverter
from messages.server_status import ServerStatusUpdateConverter
from models.user import UserView, UserCapability
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

    def supplier(self, service_type: type[DependencyT]) -> Callable[[], DependencyT]:
        """
        Returns a dependency supplier by its type.
        :param service_type: Type of the dependency to retrieve.
        :return: Dependency supplier of given type.
        """
        return lambda: self._services[service_type]

    def get(self, service_type: type[DependencyT]) -> DependencyT:
        """
        Returns a dependency by its type.
        :param service_type: Type of the dependency to retrieve.
        :return: Dependency of given type.
        """
        return self._services[service_type]


def dao_factory(config: Configuration) -> tuple[UserDao, ServerDao]:
    """Initializes data access objects."""
    match config.db_configuration:
        case SqliteDbConfiguration(db_name):
            return (
                SqliteUserDao(db_name),
                SqliteServerDao(db_name)
            )


def migrator_factory(config: Configuration) -> Callable[[],None]:
    """
    Creates callable that performs migration for configured
    persistence provider.
    """
    match config.db_configuration:
        case SqliteDbConfiguration(db_name):
            def sqlite_migrate():
                migrator.sqlite.migrate(db_name)
            return sqlite_migrate


ioc = Dependencies()


def get_current_user(
        jwt_utils: Annotated[JwtTokenUtils, Depends(ioc.supplier(JwtTokenUtils))],
        token: Annotated[Optional[str], Cookie()] = None,
) -> Optional[UserView]:
    """Returns current user if authenticated, otherwise returns None."""
    if token:
        return jwt_utils.get_user(token)
    return None


def user_with_capabilities(capabilities: list[UserCapability]):
    def get_with_capabilities(
            user: Annotated[Optional[UserView], Depends(get_current_user)]
    ) -> UserView:
        if user is None:
            raise HTTPException(status_code=401)
        for capability in capabilities:
            if capability not in user.capabilities:
                raise HTTPException(status_code=403)

        return user
    return get_with_capabilities


def rcon_converter_factory(
        templates: Annotated[TemplateProvider, Depends(ioc.supplier(TemplateProvider))],
        user: Annotated[Optional[UserView], Depends(get_current_user)],
):
    """Returns a factory for RconWSConverter for given server."""
    def create(
            server_id: uuid.UUID,
    ):
        return RconWSConverter(server_id, user.username, templates.get_template)
    return create


def status_update_converter_factory(
        templates: Annotated[TemplateProvider, Depends(ioc.supplier(TemplateProvider))],
):
    """Returns a factory for ServerStatusUpdateConverter for given server."""
    def create(
            server_id: Optional[uuid.UUID],
    ):
        return ServerStatusUpdateConverter(templates.get_template, server_id,)
    return create
