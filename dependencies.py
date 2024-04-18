import uuid
from typing import Annotated, Optional, TypeVar, Callable

from fastapi import Depends, Cookie

from auth.jwt import JwtTokenUtils
from configuration import Configuration, InMemoryDbConfiguration, SqliteDbConfiguration
from dao.server_dao import ServerDao
from dao.user_dao import UserDao
from messages.rcon import RconWSConverter
from templating import TemplateProvider

TDep = TypeVar("TDep")


class Dependencies:
    def __init__(self):
        self._services: dict[type[TDep], TDep] = dict()

    def register(self, service: TDep, register_type: Optional[type[TDep]] = None):
        service_type = register_type if register_type else type(service)
        self._services[service_type] = service

    def get(self, service_type: type[TDep]) -> Callable[[], TDep]:
        return lambda: self._services[service_type]


def initialize_dao(config: Configuration) -> tuple[UserDao, ServerDao]:
    match config.db_configuration:
        case InMemoryDbConfiguration():
            from dao.in_memory import user_dao, server_dao
            return (
                user_dao.UserDaoImpl(),
                server_dao.ServerDaoImpl()
            )
        case SqliteDbConfiguration(db_name):
            from dao.sqlite import user_dao, server_dao
            return (
                user_dao.UserDaoImpl(db_name),
                server_dao.ServerDaoImpl(db_name)
            )


ioc = Dependencies()


def get_current_user(
        jwt_utils: Annotated[JwtTokenUtils, Depends(ioc.get(JwtTokenUtils))],
        token: Annotated[Optional[str], Cookie()] = None,
) -> Optional[str]:
    if token:
        return jwt_utils.get_user(token)
    return None


def rcon_converter_factory(
        templates: Annotated[TemplateProvider, Depends(ioc.get(TemplateProvider))],
        user: Annotated[Optional[str], Depends(get_current_user)],
):
    def create(
            server_id: uuid.UUID,
    ):
        return RconWSConverter(server_id, user, templates.get_template)
    return create
