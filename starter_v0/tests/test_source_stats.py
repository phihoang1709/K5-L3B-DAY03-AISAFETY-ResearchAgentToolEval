from copy import deepcopy

import pytest

from tools.source_stats.tool import source_stats


def test_counts_lowercase_hostname_and_does_not_mutate():
    items = [{"url": "https://Example.COM/a"}, {"url": "http://example.com:8080/b"},
             {"url": "https://sub.example.com/"}, {"url": "https://[::1]/"}]
    before = deepcopy(items)
    result = source_stats(items)
    assert result["sources"] == {"example.com": 2, "sub.example.com": 1, "::1": 1}
    assert result["valid_url_count"] == 4
    assert result["missing_url_count"] == result["invalid_url_count"] == 0
    assert items == before


def test_missing_and_malformed_urls_counted_separately():
    items = [{}, {"url": None}, {"url": ""}, {"url": "   "}, {"url": 7},
             {"url": "ftp://example.com"}, {"url": "https:///x"}, {"url": "https://[bad"},
             {"url": "https://example.com:bad"}, {"url": "https://exa mple.com"},
             {"url": "https://example.com/\npath"}, {"url": "https://-bad.com"}]
    result = source_stats(items)
    assert result["sources"] == {}
    assert result["missing_url_count"] == 4
    assert result["invalid_url_count"] == 8


@pytest.mark.parametrize("items", [None, {}, "url", [None], [1]])
def test_invalid_list_returns_error(items):
    assert source_stats(items)["error"]


def test_empty_list():
    assert source_stats([]) == {"tool": "source_stats", "sources": {}, "item_count": 0,
                               "valid_url_count": 0, "missing_url_count": 0, "invalid_url_count": 0}
