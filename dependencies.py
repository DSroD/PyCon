from datetime import timedelta
from typing import Annotated

from fastapi import Depends, status, HTTPException, Cookie
from fastapi.templating import Jinja2Templates

from auth.jwt import JwtTokenUtils
from config.configuration import Configuration, InMemoryDbConfiguration, SqliteDbConfiguration
from dao.user_dao import UserDao
from messages.heartbeat import HeartbeatConverter
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

        match config.db_configuration:
            case InMemoryDbConfiguration():
                from dao.in_memory import user_dao, server_dao
                self._user_dao = user_dao.UserDaoImpl()
                self._server_dao = server_dao.ServerDaoImpl()
            case SqliteDbConfiguration(db_name):
                from dao.sqlite import user_dao
                self._user_dao = user_dao.UserDaoImpl(db_name)

    def on_start(self):
        self._user_dao.initialize()
        self._server_dao.initialize()

        self._service_launcher.launch(
            HeartbeatPublisher(
                dependencies.get_pubsub(),
                1,
            )
        )

        for server in self._server_dao.get_all():
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


configuration = Configuration()
dependencies = Dependencies(configuration)


def get_current_user(
        jwt_utils: Annotated[JwtTokenUtils, Depends(dependencies.get_jwt_utils)],
        token: Annotated[str | None, Cookie()] = None,
) -> str:
    creds_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"HX-Redirect": "/login"}
    )
    if not token:
        raise creds_exception
    username = jwt_utils.get_user(token)
    if username is None:
        raise creds_exception
    else:
        return username
