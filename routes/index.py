"""Main routes."""
# pylint: disable=too-many-function-args
from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from fastapi.websockets import WebSocket

from dependencies import get_current_user, ioc
from htmx import HtmxResponse, htmx_response_factory
from messages.heartbeat import HeartbeatConverter, heartbeat_topic
from messages.notifications import NotificationConverter, notification_topic
from models.user import UserView
from pubsub.filter import FieldEquals, FieldContains
from pubsub.pubsub import PubSub
from websocket_processor import WebsocketProcessor as WsProcessor, WebsocketPubSub

router = APIRouter()


@router.get("/", tags=["root"])
async def root(
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """UI root route."""
    return response_factory(
        template="landing.html",
    ).to_response()


@router.websocket("/heartbeat")
async def heartbeat(
        websocket: WebSocket,
        pubsub: Annotated[PubSub, Depends(ioc.supplier(PubSub))],
        heartbeat_converter: Annotated[
            HeartbeatConverter, Depends(ioc.supplier(HeartbeatConverter))
        ],
):
    """Websocket route for heartbeats."""
    await WsProcessor(
        websocket,
        heartbeat_converter,
        WebsocketPubSub(
            pubsub,
            None,
            heartbeat_topic,
        ),
    ).process()


@router.websocket("/notifications")
async def notifications(
        websocket: WebSocket,
        user: Annotated[Optional[UserView], Depends(get_current_user)],
        pubsub: Annotated[PubSub, Depends(ioc.supplier(PubSub))],
        notification_converter: Annotated[
            NotificationConverter,
            Depends(ioc.supplier(NotificationConverter))
        ],
):
    """Websocket route for notifications."""
    if not user:
        return

    await WsProcessor(
        websocket,
        notification_converter,
        WebsocketPubSub(
            pubsub,
            None,
            notification_topic,
            FieldEquals(lambda msg: msg.audience, "all")
            | FieldContains(lambda msg: msg.audience, user.username)
        ),
    ).process()
