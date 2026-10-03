"""HTML page rendering routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies.templates import get_templates

router = APIRouter()


@router.get("/")
def start_page(
    request: Request, templates: Jinja2Templates = Depends(get_templates)
) -> HTMLResponse:
    """Render the start page.

    Args:
        request: The incoming HTTP request, required by Jinja2Templates to
            build the response (e.g. for `url_for` links in the template).
        templates: The Jinja2Templates instance, injected via the templates
            dependency.

    Returns:
        The rendered start page.
    """
    return templates.TemplateResponse(
        request=request,
        name="pages/start.html",
        context={},
    )
