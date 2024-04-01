import uuid
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket

from dependencies import dependencies, get_current_user
from messages.heartbeat import HeartbeatConverter
from services.heartbeat import heartbeat_topic
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
async def root(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dependencies.get_templates)],
):
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )


@app.get("/hello/{name}")
async def say_hello(
        name: str,
        user: Annotated[str, Depends(get_current_user)]
):
    return {"message": f"Hello {name}. Your username is {user}"}


@app.websocket("/heartbeat")
async def heartbeat(
        websocket: WebSocket,
        pubsub: Annotated[PubSub, Depends(dependencies.get_pubsub)],
        heartbeat_converter: Annotated[HeartbeatConverter, Depends(dependencies.get_heartbeat_converter)],
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
