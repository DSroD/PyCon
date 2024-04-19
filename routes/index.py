from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.websockets import WebSocket

from dependencies import get_current_user, ioc
from htmx import HtmxResponse, htmx_response_factory
from messages.heartbeat import HeartbeatConverter, heartbeat_topic
from messages.notifications import NotificationConverter, notification_topic
from pubsub.filter import FieldEquals, FieldContains
from pubsub.pubsub import PubSub
from websocket_processor import WebsocketProcessor as WsProcessor

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
        pubsub: Annotated[PubSub, Depends(ioc.get(PubSub))],
        heartbeat_converter: Annotated[HeartbeatConverter, Depends(ioc.get(HeartbeatConverter))],
):
    await WsProcessor(
        websocket,
        heartbeat_converter,
        pubsub,
        None,
        heartbeat_topic,
    ).process()


@router.websocket("/notifications")
async def notifications(
        websocket: WebSocket,
        user: Annotated[str | None, Depends(get_current_user)],
        pubsub: Annotated[PubSub, Depends(ioc.get(PubSub))],
        notification_converter: Annotated[NotificationConverter, Depends(ioc.get(NotificationConverter))],
):
    if not user:
        return

    await WsProcessor(
        websocket,
        notification_converter,
        pubsub,
        None,
        notification_topic,
        FieldEquals(lambda msg: msg.audience, "all")
        | FieldContains(lambda msg: msg.audience, user)
    ).process()
