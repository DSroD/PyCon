import uuid
from datetime import timedelta
from typing import Annotated, Optional

from fastapi import Depends, Cookie
from fastapi.templating import Jinja2Templates

from auth.jwt import JwtTokenUtils
from config.configuration import Configuration, InMemoryDbConfiguration, SqliteDbConfiguration
from dao.server_dao import ServerDao
from dao.user_dao import UserDao
from messages.heartbeat import HeartbeatConverter
from messages.notifications import NotificationConverter
from messages.rcon import RconWSConverter
from services.heartbeat import HeartbeatPublisher
from pubsub.inmemory import InProcessPubSub
from pubsub.pubsub import PubSub
from rcon.echo_processor import EchoProcessor
from services.service import ServiceLauncher


class Dependencies:
    def __init__(self, config: Configuration):
        self._config = config
        self._service_launcher = ServiceLauncher()
        self._pubsub = InProcessPubSub()
        self._jwt_utils = JwtTokenUtils(
            config.access_token_secret,
            timedelta(minutes=config.access_token_expire_minutes)
        )
        self._templates = Jinja2Templates(directory="templates")
        self._heartbeat_converter = HeartbeatConverter(self._templates)
        self._notification_converter = NotificationConverter(self._templates)

        match config.db_configuration:
            case InMemoryDbConfiguration():
                from dao.in_memory import user_dao, server_dao
                self._user_dao = user_dao.UserDaoImpl()
                self._server_dao = server_dao.ServerDaoImpl()
            case SqliteDbConfiguration(db_name):
                from dao.sqlite import user_dao
                self._user_dao = user_dao.UserDaoImpl(db_name)

    async def on_start(self):
        await self._user_dao.initialize()
        await self._server_dao.initialize()

        self._service_launcher.launch(
            HeartbeatPublisher(
                dependencies.get_pubsub(),
                1,
            )
        )

        all_servers = await self._server_dao.get_all()

        # Initialize all server rcon processors
        for server in all_servers:
            self._service_launcher.launch(
                EchoProcessor(
                    dependencies.get_pubsub(),
                    server.uid,
                )
            )

    def on_stop(self):
        self._service_launcher.stop()

    def get_user_dao(self) -> UserDao:
        return self._user_dao

    def get_server_dao(self) -> ServerDao:
        return self._server_dao

    def get_pubsub(self) -> PubSub:
        return self._pubsub

    def get_service_launcher(self) -> ServiceLauncher:
        return self._service_launcher

    def get_jwt_utils(self) -> JwtTokenUtils:
        return self._jwt_utils

    def get_templates(self) -> Jinja2Templates:
        return self._templates

    def get_heartbeat_converter(self) -> HeartbeatConverter:
        return self._heartbeat_converter

    def get_notifications_converter(self) -> NotificationConverter:
        return self._notification_converter

    def get_base_template_name(self) -> str:
        return self._config.base_template_name


configuration = Configuration()
service_launcher = ServiceLauncher()
dependencies = Dependencies(configuration)


def get_current_user(
        jwt_utils: Annotated[JwtTokenUtils, Depends(dependencies.get_jwt_utils)],
        token: Annotated[Optional[str], Cookie()] = None,
) -> Optional[str]:
    if token:
        return jwt_utils.get_user(token)
    return None


def get_rcon_converter_factory(
        templates: Annotated[Jinja2Templates, Depends(dependencies.get_templates)],
        user: Annotated[Optional[str], Depends(get_current_user)],
):
    def create(
            server_id: uuid.UUID,
    ):
        return RconWSConverter(server_id, user, templates)
    return create
