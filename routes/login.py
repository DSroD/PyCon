from typing import Annotated

from fastapi import APIRouter, Response, Depends

from auth.hashing import verify_password
from auth.jwt import JwtTokenUtils
from dao.user_dao import UserDao
from dependencies import dependencies

router = APIRouter()


@router.post("/token", tags=["login"])
async def login_post(
        response: Response,
        username: str,
        password: str,
        user_dao: Annotated[UserDao, Depends(dependencies.get_user_dao)],
        token_factory: Annotated[JwtTokenUtils, Depends(dependencies.get_jwt_utils)],
):
    user = user_dao.get_with_password(username)
    if user and not user.disabled and verify_password(password, user.hashed_password):
        # TODO: put this into header instead of returning it...
        return token_factory.create_access_token(user)


@router.get("/login", tags=["login"])
async def login():
    pass
