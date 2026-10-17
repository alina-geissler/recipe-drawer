"""Tests for fetching recipe pages, with HTTP mocked by respx and DNS replaced.

respx only intercepts HTTP requests, not DNS lookups, so `resolve_hostname` is
replaced in every test; see the `resolve_to_public_address` fixture. Hostnames use
the reserved `.example` top-level domain, which never resolves in real DNS, so a
test fails loudly instead of silently using the network if the patch is missing. Like
tests/integration/test_robots_fetching.py, these tests import `httpx` although the
app uses `httpx2` (see tests/conftest.py).

Tests that only need defined routes use the `@respx.mock` decorator; without any
route, it makes every request fail the test. Tests that check that a route was not
called need `assert_all_called=False` and use the context manager form instead,
because `respx.mock(...)` with arguments creates a separate router that the
module-level `respx.get` does not reach (the respx pytest plugin and its `respx_mock`
fixture are disabled in pyproject.toml).
"""

import socket

import httpx
import pytest
import respx

from app.core.config import get_settings
from app.core.enums import FetchFailureReason
from app.extraction.fetching import MAX_REDIRECTS, FetchResult, fetch_page

PUBLIC_IP = "93.184.216.34"
LOCAL_IP = "192.168.1.1"


@pytest.fixture(autouse=True)
def resolve_to_public_address(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every hostname resolve to a public address, without a real DNS lookup.

    Patched where `check_url` looks the name up (the fetching module), not where it
    is defined. Tests that need a different result patch it again; the later patch
    wins.
    """

    def fake_resolve_hostname(_hostname: str) -> list[str]:
        return [PUBLIC_IP]

    monkeypatch.setattr(
        "app.extraction.fetching.resolve_hostname", fake_resolve_hostname
    )


# --- Page request -------------------------------------------------------------


@respx.mock
def test_returns_html_for_status_200() -> None:
    """A page answering with status 200 is returned with its HTML."""
    respx.get("https://recipes.example/pancakes").mock(
        return_value=httpx.Response(200, html="<h1>Pancakes</h1>"),
    )

    result = fetch_page("https://recipes.example/pancakes")

    assert result == FetchResult.success("<h1>Pancakes</h1>")


@respx.mock
def test_sends_configured_user_agent() -> None:
    """The page request carries the user agent from the settings."""
    route = respx.get("https://recipes.example/pancakes").mock(
        return_value=httpx.Response(200, html="<h1>Pancakes</h1>"),
    )

    fetch_page("https://recipes.example/pancakes")

    assert route.calls.last.request.headers["User-Agent"] == get_settings().user_agent


@respx.mock
@pytest.mark.parametrize("status_code", [404, 410])
def test_reports_page_not_found(status_code: int) -> None:
    """A page answering with 404 or 410 is reported as not found."""
    respx.get("https://recipes.example/pancakes").mock(
        return_value=httpx.Response(status_code),
    )

    result = fetch_page("https://recipes.example/pancakes")

    assert result == FetchResult.failure(FetchFailureReason.PAGE_NOT_FOUND)


@respx.mock
def test_reports_server_error_as_temporary_failure() -> None:
    """A page answering with a server error is reported as a temporary failure."""
    respx.get("https://recipes.example/pancakes").mock(
        return_value=httpx.Response(500),
    )

    result = fetch_page("https://recipes.example/pancakes")

    assert result == FetchResult.failure(FetchFailureReason.TEMPORARY_FAILURE)


@respx.mock
# 202 is the bot protection seen in the spike; 451 stands for any other status
@pytest.mark.parametrize("status_code", [401, 403, 429, 202, 451])
def test_reports_other_statuses_as_blocked(status_code: int) -> None:
    """A page answering with any status not handled otherwise is reported as blocked."""
    respx.get("https://recipes.example/pancakes").mock(
        return_value=httpx.Response(status_code),
    )

    result = fetch_page("https://recipes.example/pancakes")

    assert result == FetchResult.failure(FetchFailureReason.BLOCKED)


@respx.mock
@pytest.mark.parametrize(
    "exception", [httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout]
)
def test_reports_network_error_as_temporary_failure(
    exception: type[httpx.RequestError],
) -> None:
    """A connection error or timeout is reported as a temporary failure."""
    respx.get("https://recipes.example/pancakes").mock(side_effect=exception)

    result = fetch_page("https://recipes.example/pancakes")

    assert result == FetchResult.failure(FetchFailureReason.TEMPORARY_FAILURE)


# --- URL check ----------------------------------------------------------------


@respx.mock
def test_refuses_unsupported_scheme() -> None:
    """A URL with a scheme other than http or https is refused without a request.

    No route is defined, so any request would fail the test.
    """
    result = fetch_page("ftp://recipes.example/pancakes")

    assert result == FetchResult.failure(FetchFailureReason.INVALID_URL)


@respx.mock
def test_refuses_url_without_hostname() -> None:
    """A URL without a hostname is refused without a request.

    No route is defined, so any request would fail the test.
    """
    result = fetch_page("https:///pancakes")

    assert result == FetchResult.failure(FetchFailureReason.INVALID_URL)


def test_reports_unresolvable_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    """A hostname that cannot be resolved is reported without a request."""

    def fake_resolve_hostname(_hostname: str) -> list[str]:
        raise socket.gaierror

    monkeypatch.setattr(
        "app.extraction.fetching.resolve_hostname", fake_resolve_hostname
    )

    # Asserts stay inside the block: respx resets the call counts on exit.
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get("https://recipes.example/pancakes")

        result = fetch_page("https://recipes.example/pancakes")

        assert result == FetchResult.failure(FetchFailureReason.HOST_NOT_FOUND)
        assert route.call_count == 0


def test_refuses_hostname_resolving_to_local_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A hostname resolving to a local address is refused without a request."""

    def fake_resolve_hostname(_hostname: str) -> list[str]:
        return [LOCAL_IP]

    monkeypatch.setattr(
        "app.extraction.fetching.resolve_hostname", fake_resolve_hostname
    )

    # Asserts stay inside the block: respx resets the call counts on exit.
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get("https://recipes.example/pancakes")

        result = fetch_page("https://recipes.example/pancakes")

        assert result == FetchResult.failure(FetchFailureReason.LOCAL_ADDRESS)
        assert route.call_count == 0


# --- Redirects ----------------------------------------------------------------


def mock_redirect_chain(router: respx.MockRouter, *, redirects: int) -> respx.Route:
    """Mock a chain of same-origin redirects that ends with a page answering 200.

    The chain starts at https://recipes.example/hop-0 and redirects `redirects` times
    to the next hop; the last hop answers with status 200.

    Args:
        router: The respx router the routes are added to.
        redirects: Number of redirects before the page is reached.

    Returns:
        The route of the final page, so a test can check whether it was reached.
    """
    for hop in range(redirects):
        router.get(f"https://recipes.example/hop-{hop}").mock(
            return_value=httpx.Response(301, headers={"Location": f"/hop-{hop + 1}"}),
        )
    return router.get(f"https://recipes.example/hop-{redirects}").mock(
        return_value=httpx.Response(200, html="<h1>Pancakes</h1>"),
    )


def test_follows_same_origin_redirect() -> None:
    """A redirect on the same origin is followed without checking robots.txt again."""
    # Asserts stay inside the block: respx resets the call counts on exit.
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get("https://recipes.example/pancakes").mock(
            return_value=httpx.Response(301, headers={"Location": "/recipes/pancakes"}),
        )
        respx_mock.get("https://recipes.example/recipes/pancakes").mock(
            return_value=httpx.Response(200, html="<h1>Pancakes</h1>"),
        )
        robots_route = respx_mock.get("https://recipes.example/robots.txt")

        result = fetch_page("https://recipes.example/pancakes")

        assert result == FetchResult.success("<h1>Pancakes</h1>")
        assert robots_route.call_count == 0


def test_follows_cross_origin_redirect_allowed_by_robots_txt() -> None:
    """A redirect to another origin is followed if that origin's robots.txt allows it.

    Only the new origin's robots.txt is requested; the first origin's robots.txt is
    the caller's job.
    """
    # Asserts stay inside the block: respx resets the call counts on exit.
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get("https://recipes.example/pancakes").mock(
            return_value=httpx.Response(
                301, headers={"Location": "https://www.recipes.example/pancakes"}
            ),
        )
        first_robots_route = respx_mock.get("https://recipes.example/robots.txt")
        new_robots_route = respx_mock.get(
            "https://www.recipes.example/robots.txt"
        ).mock(
            return_value=httpx.Response(200, text="User-agent: *\nDisallow: /admin/"),
        )
        respx_mock.get("https://www.recipes.example/pancakes").mock(
            return_value=httpx.Response(200, html="<h1>Pancakes</h1>"),
        )

        result = fetch_page("https://recipes.example/pancakes")

        assert result == FetchResult.success("<h1>Pancakes</h1>")
        assert first_robots_route.call_count == 0
        assert new_robots_route.call_count == 1


def test_blocks_cross_origin_redirect_disallowed_by_robots_txt() -> None:
    """A redirect to another origin is blocked if that origin's robots.txt forbids it."""
    # Asserts stay inside the block: respx resets the call counts on exit.
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get("https://recipes.example/pancakes").mock(
            return_value=httpx.Response(
                301, headers={"Location": "https://www.recipes.example/pancakes"}
            ),
        )
        respx_mock.get("https://www.recipes.example/robots.txt").mock(
            return_value=httpx.Response(200, text="User-agent: *\nDisallow: /"),
        )
        page_route = respx_mock.get("https://www.recipes.example/pancakes")

        result = fetch_page("https://recipes.example/pancakes")

        assert result == FetchResult.failure(FetchFailureReason.BLOCKED)
        assert page_route.call_count == 0


def test_refuses_redirect_to_local_address_without_any_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A redirect to a local address is refused before robots.txt or the page is requested."""

    def fake_resolve_hostname(hostname: str) -> list[str]:
        if hostname == "internal.example":
            return [LOCAL_IP]
        return [PUBLIC_IP]

    monkeypatch.setattr(
        "app.extraction.fetching.resolve_hostname", fake_resolve_hostname
    )

    # Asserts stay inside the block: respx resets the call counts on exit.
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get("https://recipes.example/pancakes").mock(
            return_value=httpx.Response(
                302, headers={"Location": "http://internal.example/admin"}
            ),
        )
        robots_route = respx_mock.get("http://internal.example/robots.txt")
        page_route = respx_mock.get("http://internal.example/admin")

        result = fetch_page("https://recipes.example/pancakes")

        assert result == FetchResult.failure(FetchFailureReason.LOCAL_ADDRESS)
        assert robots_route.call_count == 0
        assert page_route.call_count == 0


@respx.mock
def test_blocks_redirect_without_location() -> None:
    """A redirect status without a Location header is reported as blocked."""
    respx.get("https://recipes.example/pancakes").mock(
        return_value=httpx.Response(301),
    )

    result = fetch_page("https://recipes.example/pancakes")

    assert result == FetchResult.failure(FetchFailureReason.BLOCKED)


def test_follows_up_to_max_redirects() -> None:
    """A chain of exactly MAX_REDIRECTS redirects is followed to the page."""
    with respx.mock() as respx_mock:
        mock_redirect_chain(respx_mock, redirects=MAX_REDIRECTS)

        result = fetch_page("https://recipes.example/hop-0")

        assert result == FetchResult.success("<h1>Pancakes</h1>")


def test_blocks_after_too_many_redirects() -> None:
    """A chain of more than MAX_REDIRECTS redirects is blocked before the page."""
    # Asserts stay inside the block: respx resets the call counts on exit.
    with respx.mock(assert_all_called=False) as respx_mock:
        page_route = mock_redirect_chain(respx_mock, redirects=MAX_REDIRECTS + 1)

        result = fetch_page("https://recipes.example/hop-0")

        assert result == FetchResult.failure(FetchFailureReason.BLOCKED)
        assert page_route.call_count == 0
