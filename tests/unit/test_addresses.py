"""Tests for resolving hostnames and checking whether IP addresses are public (SSRF)."""

import socket

import pytest

from app.extraction.addresses import are_all_addresses_public, resolve_hostname

# --- Public address check -----------------------------------------------------


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


# --- Hostname resolution ------------------------------------------------------


def test_resolve_hostname_extracts_ipv4_and_ipv6_addresses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """resolve_hostname returns the IP addresses from both IPv4 and IPv6 results."""

    def fake_getaddrinfo(*_args: object, **_kwargs: object) -> list[tuple[object, ...]]:
        # IPv4 results carry a 2-tuple (address, port), IPv6 results a 4-tuple.
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0)),
            (
                socket.AF_INET6,
                socket.SOCK_STREAM,
                6,
                "",
                ("2001:4860:4860::8888", 0, 0, 0),
            ),
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    assert resolve_hostname("recipes.example") == ["8.8.8.8", "2001:4860:4860::8888"]
