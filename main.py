import uuid
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi.websockets import WebSocket

from dependencies import dependencies
from messages.rcon import RconWSConverter, rcon_command_topic, rcon_response_topic
from pubsub.pubsub import PubSub
from routes import login, index, servers
from ws.processor import Processor as WsProcessor

app = FastAPI()

app.include_router(login.router)
app.include_router(index.router)
app.include_router(servers.router)


@app.on_event("startup")
async def startup():
    await dependencies.on_start()


@app.on_event("shutdown")
async def shutdown():
    dependencies.on_stop()
