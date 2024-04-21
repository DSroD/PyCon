"""HTML response templating."""
from dataclasses import dataclass

from fastapi.requests import Request
from fastapi.templating import Jinja2Templates


@dataclass
class ResponseMeta:
    """Metadata of the response."""
    request: Request
    headers: dict
    status_code: int


class TemplateProvider:
    """Provides Jinja2 templates."""

    def __init__(self, template_directory: str, base_template: str):
        self._templates = Jinja2Templates(directory=template_directory)
        self._base_template = base_template

    @property
    def base_template_name(self) -> str:
        """
        The name of the base template with whole page body.

        :return: Base template name
        """
        return self._base_template

    def as_response(
            self,
            template_name: str,
            context: dict,
            response_meta: ResponseMeta
    ):
        """
        Returns Response with body being rendered template.

        :param template_name: Name of the template to be rendered
        :param context: Rendering context
        :param response_meta: Response meta
        :return: Response
        """
        return self._templates.TemplateResponse(
            request=response_meta.request,
            name=template_name,
            context=context,
            headers=response_meta.headers,
            status_code=response_meta.status_code,
        )

    def get_template(self, name: str):
        """
        Returns Jinja2 Template with given name.

        :param name: Template name
        :return: Jinja2 Template
        """
        return self._templates.get_template(name)
