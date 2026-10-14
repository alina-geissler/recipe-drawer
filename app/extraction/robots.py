"""Checking whether robots.txt allows fetching a recipe page.

Contains the pure decision logic for a robots.txt response and the function that
fetches robots.txt per origin and caches the response.
"""

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx2

from app.core.config import get_settings

_robots_cache: dict[str, tuple[int, str]] = {}


def is_allowed_by_robots_txt(
    *, status_code: int, robots_txt: str, url: str, user_agent: str
) -> bool:
    """Decide whether a page may be fetched, based on the site's robots.txt response.

    The check is conservative: status 200 means the robots.txt rules are applied,
    status 404 means no robots.txt exists and fetching is allowed, and any other
    status means the page must not be fetched.

    Args:
        status_code: HTTP status code of the robots.txt response.
        robots_txt: Body of the robots.txt response.
        url: URL of the page to fetch.
        user_agent: User agent the page would be fetched with.

    Returns:
        True if the page may be fetched, False otherwise.
    """
    if status_code == 404:
        return True
    if status_code != 200:
        return False

    parser = RobotFileParser()
    parser.parse(robots_txt.splitlines())
    return parser.can_fetch(user_agent, url)


def may_fetch(url: str) -> bool:
    """Check whether a URL may be fetched according to the site's robots.txt.

    robots.txt is fetched with the configured user agent and timeout, following
    redirects. Responses are cached per origin (scheme, host and port) for the
    lifetime of the process. A failed request blocks fetching but is not cached,
    so a temporary network problem does not block a site permanently.

    Args:
        url: URL of the page to fetch.

    Returns:
        True if the page may be fetched, False otherwise.
    """
    settings = get_settings()
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    if origin in _robots_cache:
        status_code, robots_txt = _robots_cache[origin]
    else:
        try:
            response = httpx2.get(
                f"{origin}/robots.txt",
                headers={"User-Agent": settings.user_agent},
                timeout=settings.fetch_timeout_seconds,
                follow_redirects=True,
            )
            status_code, robots_txt = response.status_code, response.text
            _robots_cache[origin] = (status_code, robots_txt)
        except httpx2.RequestError:
            return False

    return is_allowed_by_robots_txt(
        status_code=status_code,
        robots_txt=robots_txt,
        url=url,
        user_agent=settings.user_agent,
    )
