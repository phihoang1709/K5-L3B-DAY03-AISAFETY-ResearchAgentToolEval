"""Regression: lists of research objects must not crash or hide reordered items."""
import importlib


def compare(monkeypatch, tmp_path, expected, actual):
    # Importing the eval runner normally loads .env; tests stay offline and isolated.
    monkeypatch.setenv("DAY03_ENV_FILE", str(tmp_path / "absent.env"))
    module = importlib.import_module("run_eval")
    return module.compare_subset(expected, actual)


def test_object_lists_match_without_sorting_dicts(monkeypatch, tmp_path):
    items = [{"title": "A"}, {"title": "B"}]
    assert compare(monkeypatch, tmp_path, {"items": items}, {"items": items})[0]


def test_object_order_and_payload_are_scored(monkeypatch, tmp_path):
    items = [{"title": "A"}, {"title": "B"}]
    assert not compare(monkeypatch, tmp_path, {"items": items}, {"items": items[::-1]})[0]
    assert not compare(monkeypatch, tmp_path, {"items": items}, {"items": [{"title": "C"}]})[0]


def test_legacy_string_list_normalization_is_preserved(monkeypatch, tmp_path):
    assert compare(monkeypatch, tmp_path, {"tags": ["AI", "B"]}, {"tags": ["b", "ai"]})[0]
