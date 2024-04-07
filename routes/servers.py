import uuid
from typing import Annotated, Callable

from fastapi import APIRouter, Depends, HTTPException, WebSocketException, status
from fastapi.websockets import WebSocket

from dao.server_dao import ServerDao
from dependencies import dependencies, get_current_user, get_rcon_converter_factory
from htmx.htmx_response import HtmxResponse, htmx_response_factory
from messages.rcon import RconWSConverter, rcon_command_topic, rcon_response_topic
from pubsub.pubsub import PubSub
from ws.processor import Processor as WsProcessor

router = APIRouter()


@router.get("/servers", tags=["servers"])
async def servers(
        server_dao: Annotated[ServerDao, Depends(dependencies.get_server_dao)],
        user: Annotated[str, Depends(get_current_user)],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    if user is None:
        raise HTTPException(status_code=401)
    user_servers = await server_dao.get_user_servers(user)
    return response_factory(
        template="servers/list.html",
        context={"servers": user_servers},
    ).to_response()


@router.get("/servers/{server_id}", tags=["servers"])
async def server(
        server_id: str,
        server_dao: Annotated[ServerDao, Depends(dependencies.get_server_dao)],
        user: Annotated[str, Depends(get_current_user)],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    if user is None:
        raise HTTPException(status_code=401)
    uid = uuid.UUID(server_id)
    server_from_db = await server_dao.get_by_uid(uid)
    if server_from_db is None:
        raise HTTPException(status_code=404)

    return response_factory(
        template="servers/detail.html",
        context={"server": server_from_db, "user": user},
    ).to_response()


@router.websocket("/rcon/{server_id}")
async def command(
        websocket: WebSocket,
        server_id: str,
        pubsub: Annotated[PubSub, Depends(dependencies.get_pubsub)],
        user: Annotated[str, Depends(get_current_user)],
        converter_factory: Annotated[Callable[[uuid.UUID], RconWSConverter], Depends(get_rcon_converter_factory)]
):
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    server_uid = uuid.UUID(server_id)

    converter = converter_factory(server_uid)
    await WsProcessor(
        websocket,
        converter,
        pubsub,
        rcon_command_topic,
        rcon_response_topic,
    ).process()
