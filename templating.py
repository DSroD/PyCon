from fastapi.requests import Request
from fastapi.templating import Jinja2Templates


class TemplateProvider:

    def __init__(self, template_directory: str, base_template: str):
        self._templates = Jinja2Templates(directory=template_directory)
        self._base_template = base_template

    @property
    def base_template_name(self) -> str:
        return self._base_template

    def as_response(
            self,
            request: Request,
            template_name: str,
            context: dict,
            headers: dict,
            status_code: int,
    ):
        return self._templates.TemplateResponse(
            request=request,
            name=template_name,
            context=context,
            headers=headers,
            status_code=status_code,
        )

    def get_template(self, name: str):
        return self._templates.get_template(name)
