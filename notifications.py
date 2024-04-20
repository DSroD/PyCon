from typing import Annotated, Optional

from fastapi import Depends

from htmx import HtmxResponse, htmx_response_factory


def notification_response_factory(
        response_factory: Annotated[type[HtmxResponse], Depends(htmx_response_factory)],
):
    """
    Returns a function that will return a HTMX notification response.
    :param response_factory: HTMX response factory
    :return:
    """
    def notification_response(
            msg: str,
            cls: Optional[str] = None,
            remove_after: Optional[int] = None,
    ):
        return response_factory(
            template="notifications/notification.html",
            context={
                "content": msg,
                "cls": cls,
                "remove_after": remove_after
            },
            push_path=False
        ).to_response()

    return notification_response
