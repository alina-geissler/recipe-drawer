"""Checking whether IP addresses are public before a page is fetched.

Protects against server-side request forgery (SSRF): the server must not be usable
to reach devices in the home network or services on the host itself.
"""

import ipaddress
import socket


def resolve_hostname(hostname: str) -> list[str]:
    """Resolve a hostname to the IP addresses a TCP connection could use.

    Only TCP results are requested, so each address appears once. Lookup errors are
    deliberately not caught: the caller decides how to react to them.

    Args:
        hostname: Hostname or IP literal, e.g. from `urlparse(url).hostname`.

    Returns:
        The resolved IP addresses as strings.

    Raises:
        socket.gaierror: If the hostname cannot be resolved.
    """
    return [
        str(info[4][0])
        for info in socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    ]


def are_all_addresses_public(addresses: list[str]) -> bool:
    """Check whether every IP address is public, so the server may connect to it.

    Implemented with the `is_global` property of the `ipaddress` module, which is
    False for private (e.g. 192.168.x.x), loopback (127.0.0.1, ::1), link-local
    (169.254.x.x) and other reserved ranges. The check fails closed: an empty list
    or a string that is not a valid IP address counts as not public.

    Args:
        addresses: IP addresses as strings, e.g. as returned by `socket.getaddrinfo`.

    Returns:
        True if the list is not empty and every address is public, False otherwise.
    """
    if not addresses:
        return False
    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        if not ip.is_global:
            return False
    return True
