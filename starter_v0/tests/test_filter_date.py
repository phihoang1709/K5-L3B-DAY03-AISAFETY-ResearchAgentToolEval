from copy import deepcopy

import pytest

from tools.filter_date.tool import filter_date


def test_inclusive_range_preserves_order_and_input():
    items = [{"date": "2024-02-29", "title": "end"},
             {"date": "2024-02-01", "title": "start"}, {"date": "2024-03-01"}]
    before = deepcopy(items)
    result = filter_date(items, "2024-02-01", "2024-02-29")
    assert result["items"] == items[:2]
    assert result["invalid_date_count"] == 0
    assert result["out_of_range_count"] == 1
    assert result["dropped_count"] == 1
    assert items == before


def test_missing_and_invalid_dates_are_counted():
    items = [{}, {"date": None}, {"date": "2023-02-29"}, {"date": "2024-2-01"},
             {"date": "20240201"}, {"date": "2024-02-01T00:00:00"}]
    result = filter_date(items, "2024-02-01", "2024-02-29")
    assert result["items"] == []
    assert result["invalid_date_count"] == result["dropped_count"] == 6


@pytest.mark.parametrize("start,end", [("2024-03-01", "2024-02-01"),
    ("2024-2-01", "2024-02-29"), (None, "2024-02-29"), ("2023-02-29", "2024-02-29")])
def test_invalid_range_returns_error(start, end):
    assert filter_date([], start, end)["error"]


@pytest.mark.parametrize("items", [None, {}, "items", [1], [{} , None]])
def test_invalid_items_return_error(items):
    assert filter_date(items, "2024-02-01", "2024-02-29")["error"]


def test_empty_list():
    assert filter_date([], "2024-02-01", "2024-02-01")["dropped_count"] == 0
