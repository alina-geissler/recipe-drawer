"""Unit tests for URL cleaning."""

import pytest

from app.extraction.url_cleaning import clean_url

# --- Tracking parameter removal ---------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/pancakes?fbclid=abc123",
        "https://example.com/pancakes?gclid=xyz789",
        "https://example.com/pancakes?igshid=42",
    ],
)
def test_removes_known_tracking_parameters(url: str) -> None:
    """clean_url strips known tracking parameters without altering the rest of the URL."""
    assert clean_url(url) == "https://example.com/pancakes"


def test_removes_utm_parameters() -> None:
    """clean_url strips UTM parameters without altering the rest of the URL."""
    url = "https://example.com/pancakes?utm_source=google&utm_medium=cpc"
    assert clean_url(url) == "https://example.com/pancakes"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://example.com/pancakes?fbclid=1&servings=4",
            "https://example.com/pancakes?servings=4",
        ),
        (
            "https://example.com/pancakes?utm_source=news&page=1",
            "https://example.com/pancakes?page=1",
        ),
        (
            "https://example.com/pancakes?my_utm_id=42",
            "https://example.com/pancakes?my_utm_id=42",
        ),
    ],
)
def test_keeps_non_tracking_parameters(url: str, expected: str) -> None:
    """clean_url keeps non-tracking parameters intact."""
    assert clean_url(url) == expected


# --- Normalization for duplicate detection -----------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("HTTPS://Example.COM/pancakes", "https://example.com/pancakes"),
        ("http://EXAMPLE.com/Pancakes", "http://example.com/Pancakes"),
    ],
)
def test_lowercases_scheme_and_host(url: str, expected: str) -> None:
    """clean_url lowercases the scheme and host but leaves the path case untouched."""
    assert clean_url(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://example.com/pancakes#wprm-recipe-container-1234",
            "https://example.com/pancakes",
        ),
        (
            "https://example.com/pancakes?servings=4#rezept",
            "https://example.com/pancakes?servings=4",
        ),
    ],
)
def test_removes_fragment(url: str, expected: str) -> None:
    """clean_url strips the fragment, with or without a query string present."""
    assert clean_url(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://example.com/pancakes/",
            "https://example.com/pancakes",
        ),
        (
            "https://example.com/recipes/pancakes/",
            "https://example.com/recipes/pancakes",
        ),
    ],
)
def test_strips_trailing_slash(url: str, expected: str) -> None:
    """clean_url strips a trailing slash from a non-root path."""
    assert clean_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/",
        "https://example.com",
    ],
)
def test_keeps_root_path_slash(url: str) -> None:
    """clean_url normalizes the root path to a single slash, with or without one given."""
    assert clean_url(url) == "https://example.com/"


def test_sorts_query_parameters() -> None:
    """clean_url sorts the remaining query parameters alphabetically by key."""
    url = "https://example.com/pancakes?servings=4&page=2"
    assert clean_url(url) == "https://example.com/pancakes?page=2&servings=4"
