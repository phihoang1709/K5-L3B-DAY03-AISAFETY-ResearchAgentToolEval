from __future__ import annotations

import re
from datetime import date
from typing import Any

from tools._shared import err


def _date(value: Any) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise ValueError("date must use YYYY-MM-DD")
    return date.fromisoformat(value)


def filter_date(items: list[dict[str, Any]] | None = None,
                start_date: str = "", end_date: str = "") -> dict[str, Any]:
    """Filter explicit dates inclusively without inferring missing dates."""
    try:
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError("items must be a list of objects")
        start, end = _date(start_date), _date(end_date)
        if start > end:
            raise ValueError("start_date must not be after end_date")
        kept = []
        invalid = outside = 0
        for item in items:
            try:
                item_date = _date(item.get("date"))
            except ValueError:
                invalid += 1
                continue
            if start <= item_date <= end:
                kept.append(item)
            else:
                outside += 1
        return {"tool": "filter_date", "items": kept, "item_count": len(items),
                "kept_count": len(kept), "invalid_date_count": invalid,
                "out_of_range_count": outside, "dropped_count": invalid + outside}
    except Exception as exc:
        return err("filter_date", exc)
