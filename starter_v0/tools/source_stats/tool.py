from __future__ import annotations

import ipaddress
import re
from typing import Any
from urllib.parse import urlsplit

from tools._shared import err


def _hostname(url: str) -> str:
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in url):
        raise ValueError("URL contains whitespace or control characters")
    parsed = urlsplit(url)
    host = parsed.hostname
    if parsed.scheme.lower() not in {"http", "https"} or not host:
        raise ValueError("URL must be HTTP(S) with a hostname")
    # Accessing port validates numeric values and the valid port range.
    _ = parsed.port
    if ":" in host:
        ipaddress.IPv6Address(host)
    else:
        ascii_host = host.encode("idna").decode("ascii").rstrip(".")
        if len(ascii_host) > 253 or any(
            not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
            for label in ascii_host.split(".")
        ):
            raise ValueError("Invalid hostname")
    return host.lower()


def source_stats(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Count HTTP(S) hosts; source frequency is not source credibility."""
    try:
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError("items must be a list of objects")
        sources: dict[str, int] = {}
        missing = invalid = 0
        for item in items:
            url = item.get("url")
            if url is None or (isinstance(url, str) and not url.strip()):
                missing += 1
                continue
            try:
                if not isinstance(url, str):
                    raise ValueError("URL must be a string")
                host = _hostname(url)
            except (ValueError, UnicodeError):
                invalid += 1
                continue
            sources[host] = sources.get(host, 0) + 1
        return {"tool": "source_stats", "sources": sources, "item_count": len(items),
                "valid_url_count": sum(sources.values()), "missing_url_count": missing,
                "invalid_url_count": invalid}
    except Exception as exc:
        return err("source_stats", exc)
