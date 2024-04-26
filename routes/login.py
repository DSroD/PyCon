"""Authentication related routes."""
# pylint: disable=too-many-function-args
from typing import Annotated, Callable, Optional

from fastapi import APIRouter, Depends, Form

from auth.hashing import verify_password
from auth.jwt import JwtTokenUtils
from dao.dao import UserDao
from dependencies import get_current_user, ioc
from htmx import htmx_response_factory, HtmxResponse, HtmxResponseMeta
from models.user import UserView
from notifications import notification_response_factory

router = APIRouter()


@router.post("/token", tags=["login"])
# pylint: disable-next=too-many-arguments
async def login_post(
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
        notification_factory: Annotated[Callable, Depends(notification_response_factory)],
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        user_dao: Annotated[UserDao, Depends(ioc.supplier(UserDao))],
        token_factory: Annotated[JwtTokenUtils, Depends(ioc.supplier(JwtTokenUtils))],
):
    """Route for login request."""
    user = await user_dao.get(username)
    if user and not user.disabled and verify_password(password, user.hashed_password):
        token = token_factory.create_access_token(user)
        return response_factory(
            template="auth/on_success.html",
            context={"msg": "Logged in successfully."},
            response_meta=HtmxResponseMeta(
                push_path=False,
                set_cookies={"token": token},
                headers={"HX-Redirect": "/"},
            )
        ).to_response()
    return notification_factory("Login failed", "bad")


@router.get("/login", tags=["login"])
async def login(
    user: Annotated[Optional[UserView], Depends(get_current_user)],
    response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """Route for logging in form."""
    if user:
        return response_factory(
            template="auth/on_success.html",
            context={"msg": "Logged in!"},
            response_meta=HtmxResponseMeta(
                headers={"HX-Redirect": "/"},
            )
        ).to_response()
    return response_factory(
        template="auth/login.html",
    ).to_response()


@router.get("/logout", tags=["login"])
async def logout(
    response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """Route for logging out current user."""
    return response_factory(
        template="auth/on_success.html",
        context={"msg": "Logged out successfully."},
        response_meta=HtmxResponseMeta(
            headers={"HX-Redirect": "/"},
            set_cookies={"token": None},
        ),
    ).to_response()
