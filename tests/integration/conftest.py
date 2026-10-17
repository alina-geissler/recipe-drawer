"""Fixtures shared by the integration tests.

The robots.txt cache is a module-level dict, so it is cleared before every test;
otherwise a response cached in one test would leak into the next.
"""

import pytest

from app.extraction.robots import _robots_cache


@pytest.fixture(autouse=True)
def clear_robots_cache() -> None:
    """Clear the robots.txt cache so no test sees responses cached by another."""
    _robots_cache.clear()
