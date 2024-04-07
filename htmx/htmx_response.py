from abc import ABC, abstractmethod
from typing import Optional, Annotated

from fastapi import HTTPException, status, Depends
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response

from dependencies import get_current_user, dependencies


class HtmxResponse(ABC):
    def __init__(
            self,
            template: str,
            context: dict = None,
            require_auth: bool = False,
            push_path: bool = True,
            headers: dict = None,
            set_cookies: dict = None,
            status_code: int = 200,
    ):
        self.template = template
        self.context = context if context else dict()
        self.require_auth = require_auth
        self.push_path = push_path
        self.headers = headers if headers else dict()
        self.set_cookies = set_cookies if set_cookies else dict()
        self.status_code = status_code

    @abstractmethod
    def to_response(self) -> Response:
        pass


def htmx_response_factory(
        request: Request,
        user: Annotated[Optional[str], Depends(get_current_user)],
        templates: Annotated[Jinja2Templates, Depends(dependencies.get_templates)],
        base_template: Annotated[str, Depends(dependencies.get_base_template_name)],
):

    class HtmxResponseImpl(HtmxResponse):
        def to_response(self) -> Jinja2Templates.TemplateResponse:
            if self.require_auth and not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized",
                    headers={"HX-Redirect": "/login"}
                )

            is_htmx = request.headers.get("HX-Request", False)
            template_name = self.template if is_htmx else base_template
            context = {"user": user, **self.context} if is_htmx else \
                {"user": user, "content_url": request.url.path}

            rendered = templates.TemplateResponse(
                request=request,
                name=template_name,
                context=context,
                headers=self.headers,
                status_code=self.status_code,
            )

            for cookie in self.set_cookies:
                rendered.set_cookie(cookie, self.set_cookies[cookie])

            if self.push_path:
                rendered.headers.append("HX-Push-Url", request.url.path)

            return rendered

    return HtmxResponseImpl
