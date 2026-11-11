from __future__ import annotations

import re
from typing import Any

from tools._shared import err


def _tokens(text: str) -> set[str]:
    # Unicode letters/numbers; underscore is a delimiter, not a token character.
    return set(re.findall(r"[^\W_]+", text.casefold()))


def rank_relevance(items: list[dict[str, Any]] | None = None,
                   query: str = "", limit: int = 5) -> dict[str, Any]:
    """Rank existing items by distinct query-token overlap, stably."""
    try:
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError("items must be a list of objects")
        if not isinstance(query, str) or not (query_tokens := _tokens(query)):
            raise ValueError("query must contain at least one letter or number")
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")
        scored = []
        for item in items:
            title, summary = item.get("title", ""), item.get("summary", "")
            if not isinstance(title, str) or not isinstance(summary, str):
                raise ValueError("title and summary must be strings when present")
            score = len(query_tokens & _tokens(title + " " + summary))
            scored.append((score, item))
        ranked = sorted(scored, key=lambda pair: -pair[0])[:limit]
        return {"tool": "rank_relevance", "items": [item for _, item in ranked],
                "scores": [score for score, _ in ranked], "item_count": len(items),
                "returned_count": len(ranked)}
    except Exception as exc:
        return err("rank_relevance", exc)
