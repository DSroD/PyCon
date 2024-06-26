"""Main module for PyConCraft app."""
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from auth.hashing import hash_password
from auth.jwt import JwtTokenUtils
from configuration import Configuration
from dao.dao import ServerDao, UserDao
from dependencies import dao_factory, ioc, migrator_factory
from messages.heartbeat import HeartbeatConverter
from messages.notifications import NotificationConverter
from models.user import UserCapability
from pubsub.inprocess import InProcessPubSub
from pubsub.pubsub import PubSub
from rcon.rcon_service import RconService
from routes import auth, index, servers, users
from services.heartbeat import HeartbeatPublisherService
from services.server_status import ServerStatusService
from services.service import ServiceLauncher
from templating import TemplateProvider

logger = logging.getLogger(__name__)

configuration = Configuration()
ioc.register(configuration)

logging.basicConfig(level=configuration.log_level)

service_launcher = ServiceLauncher(ioc)
ioc.register(service_launcher, ServiceLauncher)

pubsub: PubSub = InProcessPubSub()
ioc.register(pubsub, PubSub)

(user_dao, server_dao) = dao_factory(configuration)

ioc.register(user_dao, UserDao)
ioc.register(server_dao, ServerDao)

ioc.register(
    JwtTokenUtils(
        configuration.access_token_secret,
        timedelta(minutes=configuration.access_token_expire_minutes)
    )
)

templates = TemplateProvider(
    "templates",
    "base.html",
    {
        "all_capabilities": UserCapability,
    })
ioc.register(templates)

ioc.register(NotificationConverter(templates.get_template))
ioc.register(HeartbeatConverter(templates.get_template))


async def startup():
    """Startup logic."""
    migrate = migrator_factory(configuration)
    migrate()

    # Default user init
    # TODO: Consider better solution such as non-persisted service account
    default_user_pwd = hash_password(configuration.default_user_password)

    logger.info("Creating user %s", configuration.default_user_name)
    await user_dao.create(
        configuration.default_user_name,
        default_user_pwd,
        [
            UserCapability.USER_MANAGEMENT,
            UserCapability.SERVER_MANAGEMENT,
        ],
        None
    )

    service_launcher.launch(
        HeartbeatPublisherService(pubsub, 1)
    )

    # Watches for server status changes and provides latest state
    service_launcher.launch(
        ServerStatusService(pubsub), ServerStatusService
    )

    all_servers = await server_dao.get_all()

    def server_supplier(uid: uuid.UUID):
        def supply():
            return server_dao.get_by_uid(uid)
        return supply

    for server in all_servers:
        # Launch RCON services for all persisted servers
        service_launcher.launch(
            RconService(
                pubsub,
                server.uid,
                server_supplier(server.uid)
            )
        )


async def shutdown():
    """Shutdown logic."""
    service_launcher.stop()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """FastAPI Lifespan context manager"""
    await startup()
    yield
    await shutdown()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(index.router)
app.include_router(servers.router)
app.include_router(users.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200)
