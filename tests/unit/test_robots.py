"""Tests for the robots.txt decision logic."""

import pytest

from app.extraction.robots import is_allowed_by_robots_txt


def test_allows_when_robots_txt_not_found() -> None:
    """A missing robots.txt (404) means fetching is allowed."""
    assert is_allowed_by_robots_txt(
        status_code=404,
        robots_txt="",
        url="https://example.com/pancakes",
        user_agent="RecipeDrawerTest/1.0",
    )


@pytest.mark.parametrize("status_code", [401, 403, 429, 500, 503])
def test_blocks_on_other_status_codes(status_code: int) -> None:
    """Any status code other than 200 or 404 blocks fetching."""
    assert not is_allowed_by_robots_txt(
        status_code=status_code,
        robots_txt="",
        url="https://example.com/pancakes",
        user_agent="RecipeDrawerTest/1.0",
    )


def test_allows_path_not_disallowed_by_rules() -> None:
    """A path not covered by a Disallow rule is allowed."""
    assert is_allowed_by_robots_txt(
        status_code=200,
        robots_txt="User-agent: *\nDisallow: /admin/",
        url="https://example.com/pancakes",
        user_agent="RecipeDrawerTest/1.0",
    )


def test_blocks_path_disallowed_by_rules() -> None:
    """A path covered by a Disallow rule is blocked."""
    assert not is_allowed_by_robots_txt(
        status_code=200,
        robots_txt="User-agent: *\nDisallow: /admin/",
        url="https://example.com/admin/login",
        user_agent="RecipeDrawerTest/1.0",
    )
