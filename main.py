from datetime import timedelta

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from auth.jwt import JwtTokenUtils
from configuration import Configuration
from dao.server_dao import ServerDao
from dao.user_dao import UserDao
from dependencies import initialize_dao, ioc
from messages.heartbeat import HeartbeatConverter
from messages.notifications import NotificationConverter
from pubsub.inmemory import InProcessPubSub
from pubsub.pubsub import PubSub
from routes import login, index, servers
from services.heartbeat import HeartbeatPublisher
from services.rcon.rcon_service import RconService
from services.server_status import ServerStatusService
from services.service import ServiceLauncher
from templating import TemplateProvider

configuration = Configuration()
ioc.register(configuration)

service_launcher = ServiceLauncher(ioc)

pubsub: PubSub = InProcessPubSub()
ioc.register(pubsub, PubSub)

daos = initialize_dao(configuration)
(user_dao, server_dao) = daos

ioc.register(user_dao, UserDao),
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

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(login.router)
app.include_router(index.router)
app.include_router(servers.router)


@app.on_event("startup")
async def startup():
    for dao in daos:
        if dao:
            await dao.initialize()

    service_launcher.launch(
        HeartbeatPublisher(pubsub, 1)
    )

    service_launcher.launch(
        ServerStatusService(pubsub), ServerStatusService
    )

    all_servers = await server_dao.get_all()

    for server in all_servers:
        service_launcher.launch(
            RconService(pubsub, server)
        )


@app.on_event("shutdown")
async def shutdown():
    service_launcher.stop()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
