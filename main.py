import uuid
from typing import Annotated

from fastapi import FastAPI, Depends
from starlette.websockets import WebSocket

from dependencies import dependencies
from heartbeat.heartbeat import heartbeat_topic
from messages.heartbeat import heartbeat_converter
from messages.rcon import RconWSConverter, rcon_command_topic, rcon_response_topic
from pubsub.pubsub import PubSub
from routes import login
from ws.processor import Processor as WsProcessor

app = FastAPI()
app.include_router(login.router)


@app.on_event("startup")
async def startup():
    dependencies.on_start()


@app.on_event("shutdown")
async def shutdown():
    dependencies.on_stop()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(
        name: str,
):
    return {"message": f"Hello {name}"}


@app.websocket("/heartbeat")
async def heartbeat(
        websocket: WebSocket,
        pubsub: Annotated[PubSub, Depends(dependencies.get_pubsub)]
):
    await WsProcessor(
        websocket,
        heartbeat_converter,
        pubsub,
        None,
        heartbeat_topic,
    ).process()


@app.websocket("/command/{server_id}")
async def command(
        websocket: WebSocket,
        server_id: str,
        pubsub: Annotated[PubSub, Depends(dependencies.get_pubsub)]
):
    server_uid = uuid.UUID(server_id)
    converter = RconWSConverter(server_uid)
    await WsProcessor(
        websocket,
        converter,
        pubsub,
        rcon_command_topic,
        rcon_response_topic,
    ).process()
