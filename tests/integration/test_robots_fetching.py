"""Tests for fetching and caching robots.txt, with HTTP mocked by respx.

These tests import `httpx` although the app uses `httpx2`: tests/conftest.py makes
`httpx` resolve to httpx2 at runtime, and respx's type hints expect `httpx` types,
so mypy only accepts responses and errors created from `httpx`.
"""

import httpx
import respx

from app.core.config import get_settings
from app.extraction.robots import may_fetch


@respx.mock
def test_applies_rules_from_fetched_robots_txt() -> None:
    """The rules from the fetched robots.txt decide whether a page may be fetched."""
    respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /admin/"),
    )

    assert may_fetch("https://example.com/pancakes")
    assert not may_fetch("https://example.com/admin/login")


@respx.mock
def test_fetches_robots_txt_only_once_per_origin() -> None:
    """A second page on the same origin uses the cached robots.txt."""
    route = respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /admin/"),
    )

    assert may_fetch("https://example.com/pancakes")
    assert may_fetch("https://example.com/waffles")
    assert route.call_count == 1


@respx.mock
def test_caches_each_origin_separately() -> None:
    """Different origins do not share a cache entry."""
    route_1 = respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /admin/"),
    )
    route_2 = respx.get("https://example.org/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /admin/"),
    )

    assert may_fetch("https://example.com/pancakes")
    assert may_fetch("https://example.org/pancakes")
    assert route_1.call_count == 1
    assert route_2.call_count == 1


@respx.mock
def test_blocks_when_request_fails() -> None:
    """An unreachable robots.txt blocks fetching."""
    respx.get("https://example.com/robots.txt").mock(
        side_effect=httpx.ConnectError("Could not connect to the server"),
    )

    assert not may_fetch("https://example.com/pancakes")


@respx.mock
def test_does_not_cache_failed_requests() -> None:
    """After a failed request, the next call fetches robots.txt again."""
    route = respx.get("https://example.com/robots.txt").mock(
        side_effect=[
            httpx.ConnectError("Could not connect to the server"),
            httpx.Response(200, text="User-agent: *\nDisallow: /admin/"),
        ],
    )

    assert not may_fetch("https://example.com/pancakes")
    assert may_fetch("https://example.com/pancakes")
    assert route.call_count == 2


@respx.mock
def test_sends_configured_user_agent() -> None:
    """The robots.txt request carries the user agent from the settings."""
    route = respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /admin/"),
    )

    may_fetch("https://example.com/pancakes")
    assert route.calls.last.request.headers["User-Agent"] == get_settings().user_agent


@respx.mock
def test_follows_redirects_to_robots_txt() -> None:
    """A redirected robots.txt request is followed to the new address."""
    route_1 = respx.get("http://example.com/robots.txt").mock(
        return_value=httpx.Response(
            301, headers={"Location": "https://example.com/robots.txt"}
        ),
    )
    route_2 = respx.get("https://example.com/robots.txt").mock(
        return_value=httpx.Response(200, text="User-agent: *\nDisallow: /admin/"),
    )

    may_fetch("http://example.com/pancakes")
    assert route_1.call_count == 1
    assert route_2.call_count == 1
