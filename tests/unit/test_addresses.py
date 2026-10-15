"""Tests for the check whether IP addresses are public (SSRF protection)."""

import pytest

from app.extraction.addresses import are_all_addresses_public


@pytest.mark.parametrize("address", ["8.8.8.8", "2001:4860:4860::8888"])
def test_allows_public_addresses(address: str) -> None:
    """A public IPv4 or IPv6 address is allowed."""
    assert are_all_addresses_public(addresses=[address])


@pytest.mark.parametrize(
    "address", ["192.168.1.1", "127.0.0.1", "::1", "169.254.169.254"]
)
def test_refuses_non_public_addresses(address: str) -> None:
    """A private IPv4, loopback IPv4, loopback IPv6 or link-local address is not allowed."""
    assert not are_all_addresses_public(addresses=[address])


def test_refuses_when_any_address_is_not_public() -> None:
    """A list is refused if any address in it is not public."""
    assert not are_all_addresses_public(addresses=["8.8.8.8", "192.168.1.1"])


def test_refuses_empty_list() -> None:
    """An empty list is refused."""
    assert not are_all_addresses_public(addresses=[])


def test_refuses_invalid_address_string() -> None:
    """An invalid address string is refused."""
    assert not are_all_addresses_public(addresses=["not an address"])
