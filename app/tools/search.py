
import os

from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """Search the web and return normalized, bounded results."""

    query = query.strip()

    if len(query) < 3:
        raise ValueError("Search query must contain at least 3 characters.")

    if not 1 <= max_results <= 10:
        raise ValueError("max_results must be between 1 and 10.")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is missing. Add it to your local .env file."
        )

    client = TavilyClient(api_key=api_key)

    try:
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
            include_answer=False,
        )
    except Exception as exc:
        # Avoid exposing credentials or provider response details.
        raise RuntimeError(
            "Web search failed. Check your API key, connection, "
            "and Tavily usage limits."
        ) from None

    if not isinstance(response, dict):
        raise RuntimeError("Web search returned an invalid response.")

    results = response.get("results", [])
    if not isinstance(results, list):
        raise RuntimeError("Web search returned malformed results.")

    normalized = []

    for item in results[:max_results]:
        if not isinstance(item, dict):
            continue

        title = item.get("title")
        url = item.get("url")
        content = item.get("content")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (title, url, content)
        ):
            continue

        normalized.append(
            {
                "title": title.strip()[:300],
                "url": url.strip()[:2000],
                "content": content.strip()[:3000],
                "score": item.get("score"),
            }
        )

    return normalized
