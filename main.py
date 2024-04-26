"""Main module for PyConCraft app."""
from contextlib import asynccontextmanager
from datetime import timedelta

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from auth.hashing import hash_password
from auth.jwt import JwtTokenUtils
from configuration import Configuration
from dao.dao import ServerDao, UserDao
from dependencies import get_daos, ioc, migrator_factory
from messages.heartbeat import HeartbeatConverter
from messages.notifications import NotificationConverter
from models.user import UserCapability
from pubsub.inprocess import InProcessPubSub
from pubsub.pubsub import PubSub
from routes import login, index, servers
from services.heartbeat import HeartbeatPublisherService
from services.rcon_service import RconService
from services.server_status import ServerStatusService
from services.service import ServiceLauncher
from templating import TemplateProvider


configuration = Configuration()
ioc.register(configuration)

service_launcher = ServiceLauncher(ioc)

pubsub: PubSub = InProcessPubSub()
ioc.register(pubsub, PubSub)

(user_dao, server_dao) = get_daos(configuration)

ioc.register(user_dao, UserDao)
ioc.register(server_dao, ServerDao)

ioc.register(
    JwtTokenUtils(
        configuration.access_token_secret,
        timedelta(minutes=configuration.access_token_expire_minutes)
    )
)

templates = TemplateProvider("templates", "base.html")
ioc.register(templates)

ioc.register(NotificationConverter(templates.get_template))
ioc.register(HeartbeatConverter(templates.get_template))


async def startup():
    """Startup logic."""
    migrate = migrator_factory(configuration)
    migrate()

    # Default user init
    default_user_pwd = hash_password(configuration.default_user_password)

    await user_dao.create_user(
        configuration.default_user_name,
        default_user_pwd,
        [
            UserCapability.USER_MANAGEMENT,
            UserCapability.SERVER_MANAGEMENT,
        ]
    )

    service_launcher.launch(
        HeartbeatPublisherService(pubsub, 1)
    )

    service_launcher.launch(
        ServerStatusService(pubsub), ServerStatusService
    )

    all_servers = await server_dao.get_all()

    for server in all_servers:
        service_launcher.launch(
            RconService(pubsub, server)
        )


async def shutdown():
    """Shutdown logic."""
    service_launcher.stop()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Lifespan context manager"""
    await startup()
    yield
    await shutdown()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(login.router)
app.include_router(index.router)
app.include_router(servers.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8200)
