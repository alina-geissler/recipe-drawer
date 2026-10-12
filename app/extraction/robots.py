"""Checking whether robots.txt allows fetching a recipe page."""

from urllib.robotparser import RobotFileParser


def is_allowed(*, status_code: int, robots_txt: str, url: str, user_agent: str) -> bool:
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
