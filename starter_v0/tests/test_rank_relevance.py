from copy import deepcopy

import pytest

from tools.rank_relevance.tool import rank_relevance


def test_distinct_tokens_casefold_stable_ties_and_no_mutation():
    items = [{"title": "AI AI", "summary": "robotics"},
             {"title": "Robotics: ai"}, {"title": "chair"}, {"summary": "AI"}]
    before = deepcopy(items)
    result = rank_relevance(items, "ai AI robotics", 3)
    assert result["items"] == [items[0], items[1], items[3]]
    assert result["scores"] == [2, 2, 1]
    assert items == before


def test_unicode_and_non_alphanumeric_boundaries():
    result = rank_relevance([{"title": "STRASSE_AI"}, {"summary": "trí-tuệ"}], "Straße, trí tuệ")
    assert result["scores"] == [2, 1]
    assert result["items"][0] == {"summary": "trí-tuệ"}


@pytest.mark.parametrize("query", [None, "", "  ", "___!!!", 12])
def test_invalid_query_returns_error(query):
    assert rank_relevance([], query)["error"]


@pytest.mark.parametrize("limit", [True, False, 0, -1, 1.5, "2", None])
def test_invalid_limit_returns_error(limit):
    assert rank_relevance([], "AI", limit)["error"]


@pytest.mark.parametrize("items", [None, {}, [None], [{"title": 12}], [{"summary": []}]])
def test_invalid_items_return_error(items):
    assert rank_relevance(items, "AI")["error"]


def test_empty_list_and_zero_score_items():
    assert rank_relevance([], "AI")["items"] == []
    assert rank_relevance([{}, {"title": "chair"}], "AI")["scores"] == [0, 0]
