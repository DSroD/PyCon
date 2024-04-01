from typing import Annotated, Optional

from fastapi import Depends
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

from dependencies import dependencies


def notification_response(
    templates: Annotated[Jinja2Templates, Depends(dependencies.get_templates)],
):
    def get_response(
            request: Request,
            msg: str,
            cls: Optional[str] = None,
            remove_after: Optional[int] = None,
    ):
        return templates.TemplateResponse(
            request=request,
            name="notifications/notification.html",
            context={
                "content": msg,
                "cls": cls,
                "remove_after": remove_after
            }
        )
    return get_response
