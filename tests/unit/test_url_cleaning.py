"""Unit tests for URL cleaning."""

import pytest

from app.extraction.url_cleaning import clean_url


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
