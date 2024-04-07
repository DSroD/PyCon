from typing import Annotated, Callable

from fastapi import APIRouter, Depends, Form

from auth.hashing import verify_password
from auth.jwt import JwtTokenUtils
from dao.user_dao import UserDao
from dependencies import dependencies, get_current_user
from htmx.htmx_response import htmx_response_factory, HtmxResponse
from notifications.notification_response import notification_response_factory

router = APIRouter()


@router.post("/token", tags=["login"])
async def login_post(
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
        notification_factory: Annotated[Callable, Depends(notification_response_factory)],
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        user_dao: Annotated[UserDao, Depends(dependencies.get_user_dao)],
        token_factory: Annotated[JwtTokenUtils, Depends(dependencies.get_jwt_utils)],
):
    user = await user_dao.get_with_password(username)
    if user and not user.disabled and verify_password(password, user.hashed_password):
        token = token_factory.create_access_token(user)
        return response_factory(
            template="auth/on_success.html",
            push_path=False,
            set_cookies={"token": token},
            context={"msg": "Logged in successfully."},
            headers={"HX-Redirect": "/"},
        ).to_response()
    return notification_factory("Login failed", "bad")


@router.get("/login", tags=["login"])
async def login(
    user: Annotated[str, Depends(get_current_user)],
    response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    if user:
        return response_factory(
            template="auth/on_success.html",
            context={"msg": "Logged in!"},
            headers={"HX-Redirect": "/"},
        ).to_response()
    return response_factory(
        template="auth/login.html",
    ).to_response()


@router.get("/logout", tags=["login"])
async def logout(
    response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    return response_factory(
        template="auth/on_success.html",
        set_cookies={"token": None},
        context={"msg": "Logged out successfully."},
        headers={"HX-Redirect": "/"},
    ).to_response()

