
import pytest

from app.tools import search


def test_short_query_is_rejected():
    with pytest.raises(ValueError):
        search.search_web("  ")


def test_invalid_result_limit_is_rejected():
    with pytest.raises(ValueError):
        search.search_web("Python research", max_results=20)


def test_missing_api_key_is_reported(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="TAVILY_API_KEY is missing"):
        search.search_web("Python research")


def test_search_results_are_normalized(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    class FakeTavilyClient:
        def __init__(self, api_key):
            assert api_key == "test-key"

        def search(self, **kwargs):
            assert kwargs["max_results"] == 2
            return {
                "results": [
                    {
                        "title": "Python Documentation",
                        "url": "https://docs.python.org/",
                        "content": "Official Python documentation.",
                        "score": 0.95,
                    },
                    {
                        "title": "Incomplete result",
                        "url": "https://example.com/",
                    },
                ]
            }

    monkeypatch.setattr(
        search, "TavilyClient", FakeTavilyClient
    )

    results = search.search_web("Python documentation", max_results=2)

    assert len(results) == 1
    assert results[0]["title"] == "Python Documentation"
    assert results[0]["score"] == 0.95
