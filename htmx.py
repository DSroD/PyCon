"""HTMX response related classes and functions."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Annotated, override

from fastapi import HTTPException, status, Depends
from fastapi.requests import Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates

from dependencies import get_current_user, ioc
from models.user import UserView
from templating import TemplateProvider, ResponseMeta


@dataclass(frozen=True, eq=True)
class CookieMeta:
    """
    Cookie metadata for HTMX responses.

    :param expires: Number of seconds until the cookie expires.
    """
    name: str
    value: Optional[str]
    expires: Optional[int] = None


@dataclass(frozen=True)
class HtmxResponseMeta:
    """Metadata tied to a HtmxResponse."""
    require_auth: bool = False
    push_path: bool = True
    headers: dict[str, str] = field(default_factory=dict)
    set_cookies: list[CookieMeta] = field(default_factory=list)
    status_code: int = 200


class HtmxResponse(ABC):
    """Abstract base class for HTMX response wrapper."""
    def __init__(
            self,
            template: str,
            context: dict = None,
            response_meta: HtmxResponseMeta = HtmxResponseMeta(),
    ):
        self._template = template
        self._context = context if context else {}
        self._response_meta = response_meta

    @abstractmethod
    def to_response(self) -> Response:
        """Creates response from HtmxResponse"""


def htmx_response_factory(
        request: Request,
        user: Annotated[Optional[UserView], Depends(get_current_user)],
        templates: Annotated[TemplateProvider, Depends(ioc.supplier(TemplateProvider))],
):
    """Factory for HTMX responses."""
    class HtmxResponseImpl(HtmxResponse):
        """Creates response from HtmxResponse"""
        @override
        def to_response(self) -> Jinja2Templates.TemplateResponse:
            """Creates a response with HTMX content."""
            if self._response_meta.require_auth and not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized",
                    headers={"HX-Redirect": "/login"}
                )

            is_htmx = request.headers.get("HX-Request", False)
            template_name = self._template if is_htmx else templates.base_template_name
            context = {
                "user": user,
                **self._context
            } if is_htmx else {
                "user": user,
                "content_url": request.url.path
            }

            rendered = templates.as_response(
                template_name=template_name,
                context=context,
                response_meta=ResponseMeta(
                    request, self._response_meta.headers, self._response_meta.status_code
                ),
            )

            for cookie in self._response_meta.set_cookies:
                rendered.set_cookie(cookie.name, cookie.value, expires=cookie.expires)

            if self._response_meta.push_path:
                rendered.headers.append("HX-Push-Url", request.url.path)

            return rendered

    return HtmxResponseImpl
