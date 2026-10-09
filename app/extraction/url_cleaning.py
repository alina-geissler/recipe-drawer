"""Cleaning and normalizing of recipe URLs."""

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_PARAMS = (
    "igshid",
    "fbclid",
    "gclid",
    "gbraid",
    "wbraid",
    "ttclid",
    "twclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
)


def clean_url(url: str) -> str:
    """Clean and normalize a URL for storage and duplicate detection.

    Removes tracking parameters in `TRACKING_PARAMS` (matched by exact name)
    and any parameter starting with `utm_`. Lowercases the scheme and host
    (the path is left unchanged). Strips the fragment, strips a trailing
    slash from non-root paths, and sorts the remaining query parameters
    alphabetically by key.

    Args:
        url: The URL to clean.

    Returns:
        The cleaned and normalized URL.
    """
    parsed_url = urlparse(url)

    kept_params = []
    for key, value in parse_qsl(parsed_url.query):
        if key not in TRACKING_PARAMS and not key.startswith("utm_"):
            kept_params.append((key, value))

    kept_params.sort()

    normalized_scheme = parsed_url.scheme.lower()
    normalized_host = parsed_url.netloc.lower()

    normalized_path = parsed_url.path
    if not normalized_path:
        normalized_path = "/"
    elif normalized_path.endswith("/") and len(normalized_path) > 1:
        normalized_path = normalized_path[:-1]

    return urlunparse(
        parsed_url._replace(
            query=urlencode(kept_params),
            scheme=normalized_scheme,
            netloc=normalized_host,
            fragment="",
            path=normalized_path,
        )
    )
