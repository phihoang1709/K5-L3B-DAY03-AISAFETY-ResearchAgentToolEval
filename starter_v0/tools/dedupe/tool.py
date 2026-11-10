from __future__ import annotations

from typing import Any

from tools._shared import err


def _identity(item: dict[str, Any]) -> tuple[str, str] | None:
    url = item.get("url")
    if isinstance(url, str) and url.strip():
        return ("url", url.strip().rstrip("/").lower())

    title = item.get("title")
    if isinstance(title, str) and title.strip():
        return ("title", " ".join(title.split()).casefold())

    return None


def dedupe_items(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Remove duplicate research items while preserving first-seen order."""
    try:
        if not isinstance(items, list):
            raise ValueError("items must be a list")

        unique: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("every item must be an object")

            identity = _identity(item)
            if identity is not None and identity in seen:
                continue
            if identity is not None:
                seen.add(identity)
            unique.append(item)

        return {
            "tool": "dedupe",
            "items": unique,
            "item_count": len(items),
            "unique_count": len(unique),
            "duplicates_removed": len(items) - len(unique),
        }
    except Exception as exc:
        return err("dedupe", exc)
