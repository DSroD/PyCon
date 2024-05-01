"""Servers related routes."""
# pylint: disable=too-many-function-args,too-many-arguments
import uuid
from typing import Annotated, Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocketException, status, Form
from fastapi.websockets import WebSocket

from dao.dao import ServerDao, UserDao
from dependencies import (
    get_current_user,
    rcon_converter_factory,
    ioc,
    status_update_converter_factory, user_with_capabilities
)
from htmx import HtmxResponse, htmx_response_factory
from messages.rcon import RconWSConverter, rcon_command_topic, rcon_response_topic
from messages.server_status import ServerStatusUpdateConverter, server_status_topic
from models.server import Server, from_form_data
from models.user import UserView, UserCapability
from pubsub.filter import FieldEquals
from pubsub.pubsub import PubSub
from services.rcon_service import RconService, rcon_service_name
from services.server_status import ServerStatusService
from services.service import ServiceLauncher
from websocket_processor import WebsocketProcessor as WsProcessor, WebsocketPubSub

router = APIRouter()


@router.get("/servers", tags=["servers"])
async def servers_index(
    server_dao: Annotated[ServerDao, Depends(ioc.supplier(ServerDao))],
    user: Annotated[Optional[UserView], Depends(user_with_capabilities([]))],
    response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
    server_status_service: Annotated[
        ServerStatusService,
        Depends(ioc.supplier(ServerStatusService))
    ]
):
    """Route for getting all servers list."""
    user_servers = await server_dao.get_user_servers(user.username)
    server_statuses = server_status_service.get_states({s.uid for s in user_servers})

    return response_factory(
        template="servers/list.html",
        context={
            "servers": user_servers,
            "statuses": server_statuses
        },
    ).to_response()


@router.get("/servers/{server_id}", tags=["servers"])
async def server_view(
    _: Annotated[Optional[UserView], Depends(user_with_capabilities([]))],
    server_id: str,
    server_dao: Annotated[ServerDao, Depends(ioc.supplier(ServerDao))],
    response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
    server_status_service: Annotated[
        ServerStatusService,
        Depends(ioc.supplier(ServerStatusService))
    ]
):
    """Route for getting a specific server detail by id."""
    try:
        uid = uuid.UUID(server_id)
    except ValueError as exc:
        raise HTTPException(status_code=404) from exc

    server_from_db = await server_dao.get_by_uid(uid)
    if server_from_db is None:
        raise HTTPException(status_code=404)

    server_status = server_status_service.get_state(uid)

    return response_factory(
        template="servers/detail.html",
        context={
            "server": server_from_db,
            "server_status": server_status
        },
    ).to_response()


@router.get("/server-mgmt", tags=["management"])
async def server_management_index(
    _: Annotated[
        Optional[UserView],
        Depends(user_with_capabilities([UserCapability.SERVER_MANAGEMENT]))
    ],
    server_dao: Annotated[ServerDao, Depends(ioc.supplier(ServerDao))],
    response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """Route for index page of servers management."""
    servers = await server_dao.get_all()

    return response_factory(
        template="management/server_management_index.html",
        context={"servers": servers}
    ).to_response()


@router.get("/server-mgmt/edit/", tags=["server-management"])
async def server_management_edit(
        _: Annotated[
            Optional[UserView],
            Depends(user_with_capabilities([UserCapability.SERVER_MANAGEMENT]))
        ],
        server_dao: Annotated[ServerDao, Depends(ioc.supplier(ServerDao))],
        user_dao: Annotated[UserDao, Depends(ioc.supplier(UserDao))],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
        uid: Optional[str] = None,
):
    """Route for editing a specific server."""
    server_uid = uuid.UUID(uid) if uid else None
    server = await server_dao.get_by_uid(server_uid) if server_uid else None
    usernames = await user_dao.get_all_usernames()
    selected_usernames = await server_dao.get_assigned_usernames(server_uid) if server_uid else []

    return response_factory(
        template="management/server_management_edit.html",
        context={
            "server": server,
            "usernames": usernames,
            "selected_usernames": selected_usernames
        },
    ).to_response()


@router.put("/server-mgmt/edit/", tags=["server-management"])
async def server_management_upsert(
        user: Annotated[
            Optional[UserView],
            Depends(user_with_capabilities([UserCapability.SERVER_MANAGEMENT]))
        ],
        server: Annotated[Server, Depends(from_form_data)],
        server_users: Annotated[list[str], Form()],
        server_dao: Annotated[ServerDao, Depends(ioc.supplier(ServerDao))],
        service_launcher: Annotated[ServiceLauncher, Depends(ioc.supplier(ServiceLauncher))],
        pubsub: Annotated[PubSub, Depends(ioc.supplier(PubSub))],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """Route for upserting a server."""
    await server_dao.upsert(server, user.username)
    await server_dao.set_assigned_users(server.uid, server_users, user.username)

    name = rcon_service_name(server.uid)

    if service_launcher.is_running(name):
        service_launcher.stop_service(name)

    def server_supplier():
        return server_dao.get_by_uid(server.uid)

    service_launcher.launch(
        RconService(
            pubsub,
            server.uid,
            server_supplier
        )
    )

    return response_factory(
        template="management/server_management_success.html",
    ).to_response()


@router.delete("/server-mgmt/{uid}", tags=["server-management"])
async def server_management_delete(
        uid: str,
        user: Annotated[
            Optional[UserView],
            Depends(user_with_capabilities([UserCapability.SERVER_MANAGEMENT]))
        ],
        server_dao: Annotated[ServerDao, Depends(ioc.supplier(ServerDao))],
        service_launcher: Annotated[ServiceLauncher, Depends(ioc.supplier(ServiceLauncher))],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """Route for deleting a server"""
    server_uid = uuid.UUID(uid)

    name = rcon_service_name(server_uid)

    service_launcher.stop_service(name)

    await server_dao.delete(server_uid, user.username)

    return response_factory(
        template="management/server_management_success.html",
    ).to_response()


@router.websocket("/servers/updates")
async def updates(
    websocket: WebSocket,
    pubsub: Annotated[PubSub, Depends(ioc.supplier(PubSub))],
    user: Annotated[Optional[UserView], Depends(get_current_user)],
    converter_factory: Annotated[Callable[
        [Optional[uuid.UUID]],
        ServerStatusUpdateConverter],
        Depends(status_update_converter_factory)
    ],
):
    """Websocket route for updating server status in servers list."""
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    converter = converter_factory(None)
    await WsProcessor(
        websocket,
        converter,
        WebsocketPubSub(
            pubsub,
            None,
            server_status_topic,
        )
    ).process()


@router.websocket("/servers/updates/{server_id}")
async def detail_updates(
    websocket: WebSocket,
    server_id: str,
    pubsub: Annotated[PubSub, Depends(ioc.supplier(PubSub))],
    user: Annotated[Optional[UserView], Depends(get_current_user)],
    converter_factory: Annotated[Callable[
        [Optional[uuid.UUID]],
        ServerStatusUpdateConverter],
        Depends(status_update_converter_factory)
    ],
):
    """Websocket route for updating server status to a specific server detail."""
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    uid = uuid.UUID(server_id)

    converter = converter_factory(uid)
    await WsProcessor(
        websocket,
        converter,
        WebsocketPubSub(
            pubsub,
            None,
            server_status_topic,
            FieldEquals(lambda msg: msg.server_uid, uid),
        ),
    ).process()


@router.websocket("/rcon/{server_id}")
async def command(
    websocket: WebSocket,
    server_id: str,
    pubsub: Annotated[PubSub, Depends(ioc.supplier(PubSub))],
    user: Annotated[Optional[UserView], Depends(get_current_user)],
    converter_factory: Annotated[
        Callable[[uuid.UUID], RconWSConverter],
        Depends(rcon_converter_factory)
    ]
):
    """Websocket route for handling RCON commands."""
    if user is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    server_uid = uuid.UUID(server_id)

    converter = converter_factory(server_uid)
    await WsProcessor(
        websocket,
        converter,
        WebsocketPubSub(
            pubsub,
            rcon_command_topic(server_uid),
            rcon_response_topic(server_uid),
        ),
    ).process()
