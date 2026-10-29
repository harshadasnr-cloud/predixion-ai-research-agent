
import os

from dotenv import load_dotenv
from google import genai

from app.tools.search import search_web

load_dotenv()


def check_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    if not api_key:
        print("Gemini: FAIL — GEMINI_API_KEY is missing.")
        return False

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents="Reply with exactly: OK",
        )

        if response.text:
            print(f"Gemini: PASS — API request succeeded using {model}.")
            return True

        print("Gemini: FAIL — The API returned an empty response.")
        return False

    except Exception as exc:
        print(f"Gemini: FAIL — {type(exc).__name__}")
        return False


def check_tavily():
    if not os.getenv("TAVILY_API_KEY"):
        print("Tavily: FAIL — TAVILY_API_KEY is missing.")
        return False

    try:
        results = search_web("Python programming language", max_results=1)

        if results:
            print("Tavily: PASS — Web search succeeded.")
            return True

        print("Tavily: FAIL — Search returned no results.")
        return False

    except Exception as exc:
        print(f"Tavily: FAIL — {type(exc).__name__}")
        return False


if __name__ == "__main__":
    gemini_ok = check_gemini()
    tavily_ok = check_tavily()

    if not (gemini_ok and tavily_ok):
        raise SystemExit(1)

    print("All external service checks passed.")
