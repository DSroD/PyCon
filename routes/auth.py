"""Authentication related routes."""
from typing import Annotated, Callable, Optional

from fastapi import APIRouter, Depends, Form
from fastapi.responses import Response

from auth.hashing import verify_password
from auth.jwt import JwtTokenUtils
from configuration import Configuration
from dao.dao import UserDao
from dependencies import get_current_user, ioc
from htmx import htmx_response_factory, notification_response_factory, HtmxResponse, HtmxResponseMeta, CookieMeta
from models.user import UserView

router = APIRouter()


@router.post("/token", tags=["auth"])
# pylint: disable-next=too-many-arguments
async def login_post(
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
        notification_factory: Annotated[Callable, Depends(notification_response_factory)],
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        user_dao: Annotated[UserDao, Depends(ioc.supplier(UserDao))],
        token_factory: Annotated[JwtTokenUtils, Depends(ioc.supplier(JwtTokenUtils))],
        configuration: Annotated[Configuration, Depends(ioc.supplier(Configuration))],
):
    """Route for login request."""
    user = await user_dao.get(username)
    if user and not user.disabled and verify_password(password, user.hashed_password):
        token = token_factory.create_access_token(user)
        token_duration_seconds = configuration.access_token_expire_minutes * 60
        return response_factory(
            template="auth/auth_success.html",
            context={"msg": "Logged in successfully."},
            response_meta=HtmxResponseMeta(
                push_path=False,
                set_cookies=[CookieMeta("token", token, token_duration_seconds)],
                headers={"HX-Redirect": "/"},
            )
        ).to_response()
    return notification_factory("Login failed", "bad")


@router.get("/login", tags=["auth"])
async def login(
        user: Annotated[Optional[UserView], Depends(get_current_user)],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """Route for logging in form."""
    if user:
        return response_factory(
            template="auth/auth_success.html",
            context={"msg": "Logged in!"},
            response_meta=HtmxResponseMeta(
                headers={"HX-Redirect": "/"},
            )
        ).to_response()
    return response_factory(
        template="auth/login.html",
    ).to_response()


@router.get("/logout", tags=["auth"])
async def logout(
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """Route for logging out current user."""
    return response_factory(
        template="auth/auth_success.html",
        context={"msg": "Logged out successfully."},
        response_meta=HtmxResponseMeta(
            headers={"HX-Redirect": "/"},
            set_cookies=[CookieMeta("token", None)],
        ),
    ).to_response()


@router.get("/refresh", tags=["auth"])
async def refresh(
        response: Response,
        user: Annotated[Optional[UserView], Depends(get_current_user)],
        token_factory: Annotated[JwtTokenUtils, Depends(ioc.supplier(JwtTokenUtils))],
        configuration: Annotated[Configuration, Depends(ioc.supplier(Configuration))],
        user_dao: Annotated[UserDao, Depends(ioc.supplier(UserDao))],
):
    """Route for refreshing authentication cookie"""
    if user:
        user_in_db = await user_dao.get_view(user.username)
        # Checks if user still exists and is still enabled
        if user_in_db is None:
            return
        token = token_factory.create_access_token(user)
        token_duration_seconds = configuration.access_token_expire_minutes * 60
        response.set_cookie("token", token, expires=token_duration_seconds)
        response.status_code = 204
        return response
