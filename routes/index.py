from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.websockets import WebSocket

from dependencies import dependencies
from htmx.htmx_response import HtmxResponse, htmx_response_factory
from messages.heartbeat import HeartbeatConverter, heartbeat_topic
from pubsub.pubsub import PubSub
from ws.processor import Processor as WsProcessor

router = APIRouter()


@router.get("/", tags=["root"])
async def root(
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    return response_factory(
        template="landing.html",
    ).to_response()


@router.websocket("/heartbeat")
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
