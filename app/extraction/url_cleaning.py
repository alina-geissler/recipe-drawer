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
    """Remove known tracking parameters from a URL.

    Matches parameters in `TRACKING_PARAMS` by exact name, and any parameter
    starting with `utm_`.

    Args:
        url: The URL to clean.

    Returns:
        The URL with tracking parameters removed.
    """
    parsed_url = urlparse(url)
    kept_params = []
    for key, value in parse_qsl(parsed_url.query):
        if key not in TRACKING_PARAMS and not key.startswith("utm_"):
            kept_params.append((key, value))
    return urlunparse(parsed_url._replace(query=urlencode(kept_params)))
