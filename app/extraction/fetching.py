"""Fetching recipe pages with SSRF protection.

Contains the check that every URL must pass before it is requested and the function
that fetches a page, following redirects manually so each hop is checked.
"""

import socket
from dataclasses import dataclass
from typing import Self
from urllib.parse import urlparse

import httpx2

from app.core.config import get_settings
from app.core.enums import FetchFailureReason
from app.extraction.addresses import are_all_addresses_public, resolve_hostname
from app.extraction.robots import may_fetch
from app.extraction.url_cleaning import get_origin

MAX_REDIRECTS = 5


def check_url(url: str) -> FetchFailureReason | None:
    """Check whether a URL may be requested at all (SSRF protection, plan section 11.3).

    The URL must use http or https, have a hostname, resolve, and every resolved IP
    address must be public.

    This check is deliberately called in several places: by the link-import service
    before robots.txt is checked (pipeline step 3), and by the fetcher for the first
    URL and for every redirect hop. The repeated calls are not duplication: every
    outgoing request is checked, regardless of whether a caller has already done so.

    Args:
        url: URL that is about to be requested.

    Returns:
        The failure reason if the URL must not be requested, None if it may be.
    """
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    if not hostname:
        return FetchFailureReason.INVALID_URL
    if parsed_url.scheme not in ("http", "https"):
        return FetchFailureReason.INVALID_URL
    try:
        addresses = resolve_hostname(hostname)
    except socket.gaierror:
        return FetchFailureReason.HOST_NOT_FOUND
    if not are_all_addresses_public(addresses):
        return FetchFailureReason.LOCAL_ADDRESS
    return None


@dataclass(frozen=True)
class FetchResult:
    """Outcome of fetching a page: either the HTML or the reason it failed.

    Create instances with `success` or `failure`, so exactly one field is set.
    """

    html: str | None = None
    reason: FetchFailureReason | None = None

    @classmethod
    def success(cls, html: str) -> Self:
        """Create a result for a successfully fetched page."""
        return cls(html=html)

    @classmethod
    def failure(cls, reason: FetchFailureReason) -> Self:
        """Create a result for a failed fetch."""
        return cls(reason=reason)


def fetch_page(url: str) -> FetchResult:
    """Fetch a recipe page with the configured user agent and timeout.

    Redirects are followed manually, at most `MAX_REDIRECTS` times. Every URL,
    including the first and every redirect target, must pass `check_url` before it
    is requested, and robots.txt is checked again when a redirect leads to another
    origin. The robots.txt check for the first URL is the caller's job
    (pipeline step 4).

    Only status 200 counts as success; how other statuses map to failure reasons is
    described in plan section 7.3.

    Args:
        url: URL of the recipe page.

    Returns:
        The page's HTML on success, otherwise the reason the fetch failed.
    """
    settings = get_settings()
    for _ in range(MAX_REDIRECTS + 1):
        failure_reason = check_url(url)
        if failure_reason is not None:
            return FetchResult.failure(failure_reason)
        try:
            response = httpx2.get(
                url,
                headers={"User-Agent": settings.user_agent},
                timeout=settings.fetch_timeout_seconds,
                follow_redirects=False,
            )
        except httpx2.RequestError:
            return FetchResult.failure(FetchFailureReason.TEMPORARY_FAILURE)
        if response.is_redirect:
            next_request = response.next_request
            if not next_request:
                # redirect without a usable Location header
                return FetchResult.failure(FetchFailureReason.BLOCKED)
            redirect_to = str(next_request.url)
            origin_current = get_origin(url)
            origin_next = get_origin(redirect_to)
            if origin_current != origin_next:
                # Checked here as well as at the top of the loop: may_fetch is itself an
                # outgoing request and must not reach a local address.
                failure_reason = check_url(redirect_to)
                if failure_reason is not None:
                    return FetchResult.failure(failure_reason)
                if not may_fetch(redirect_to):
                    # forbidden by robots.txt
                    return FetchResult.failure(FetchFailureReason.BLOCKED)
            url = redirect_to
            continue
        if response.status_code == 200:
            return FetchResult.success(response.text)
        if response.status_code in (404, 410):
            return FetchResult.failure(FetchFailureReason.PAGE_NOT_FOUND)
        if response.status_code >= 500:
            return FetchResult.failure(FetchFailureReason.TEMPORARY_FAILURE)
        # 401, 403, 429, bot protection and any other status
        return FetchResult.failure(FetchFailureReason.BLOCKED)
    return FetchResult.failure(FetchFailureReason.BLOCKED)  # too many redirects
