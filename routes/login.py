from typing import Annotated, Callable

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from auth.hashing import verify_password
from auth.jwt import JwtTokenUtils
from dao.user_dao import UserDao
from dependencies import dependencies
from notifications.notification_response import notification_response

router = APIRouter()


@router.post("/token", tags=["login"])
async def login_post(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        user_dao: Annotated[UserDao, Depends(dependencies.get_user_dao)],
        token_factory: Annotated[JwtTokenUtils, Depends(dependencies.get_jwt_utils)],
        notification: Annotated[Callable, Depends(notification_response)],
):
    user = user_dao.get_with_password(username)
    if user and not user.disabled and verify_password(password, user.hashed_password):
        token = token_factory.create_access_token(user)
        response = notification(request, "Login successful", "ok")
        response.set_cookie("token", token, httponly=True)
        return response
    return notification(request, "Login failed", "bad")


@router.get("/login", tags=["login"], response_class=HTMLResponse)
async def login(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(dependencies.get_templates)],
):
    return templates.TemplateResponse(
        request=request, name="auth/login.html", context={},
    )
