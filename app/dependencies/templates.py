"""Provide the shared Jinja2Templates instance as a FastAPI dependency."""

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def get_templates() -> Jinja2Templates:
    """Return the shared Jinja2Templates instance.

    Returns:
        The configured Jinja2Templates instance used to render HTML responses.
    """
    return templates
