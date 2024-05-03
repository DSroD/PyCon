"""User related routes"""
# pylint: disable=too-many-function-args,too-many-arguments
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request

from dao.dao import UserDao
from dependencies import user_with_capabilities, ioc
from htmx import HtmxResponse, htmx_response_factory
from models.user import UserView, UserCapability, UserUpsert, from_form_data

router = APIRouter()


@router.get("/user-mgmt", tags=["user-mgmt"])
async def user_management_index(
        _: Annotated[
            Optional[UserView],
            Depends(user_with_capabilities([UserCapability.USER_MANAGEMENT]))
        ],
        user_dao: Annotated[UserDao, Depends(ioc.supplier(UserDao))],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)]
):
    """Route for index page of user management"""
    usernames = await user_dao.get_all_usernames()

    return response_factory(
        template="management/user_management_index.html",
        context={"usernames": usernames}
    ).to_response()


@router.get("/user-mgmt/edit", tags=["user-management"])
async def user_management_edit(
        _: Annotated[
            Optional[UserView],
            Depends(user_with_capabilities([UserCapability.USER_MANAGEMENT]))
        ],
        user_dao: Annotated[UserDao, Depends(ioc.supplier(UserDao))],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
        user: Optional[str] = None,
):
    """Route for editing a specific server"""
    user = await user_dao.get(user) if user else None

    return response_factory(
        template="management/user_management_edit.html",
        context={
            "user": user
        }
    ).to_response()


@router.post("/user-mgmt/edit", tags=["user-management"])
async def user_management_upsert(
        current_user: Annotated[
            Optional[UserView],
            Depends(user_with_capabilities([UserCapability.USER_MANAGEMENT]))
        ],
        upsert: Annotated[UserUpsert, Depends(from_form_data)],
        user_dao: Annotated[UserDao, Depends(ioc.supplier(UserDao))],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """Route for upserting a user"""
    await user_dao.upsert(upsert, current_user.username)

    return response_factory(
        template="management/management_success.html",
        context={"route": "/user-mgmt/"}
    ).to_response()


@router.delete("/user-mgmt/{username}", tags=["user-management"])
async def user_management_delete(
        request: Request,
        current_user: Annotated[
            Optional[UserView],
            Depends(user_with_capabilities([UserCapability.USER_MANAGEMENT]))
        ],
        username: str,
        user_dao: Annotated[UserDao, Depends(ioc.supplier(UserDao))],
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """Route for deleting a specific user"""
    prompted_name = request.headers.get("HX-Prompt", None)

    if prompted_name != username:
        raise HTTPException(status_code=400)

    await user_dao.delete(username, current_user.username)

    return response_factory(
        template="management/management_success.html",
        context={"route": "/user-mgmt/"}
    ).to_response()
