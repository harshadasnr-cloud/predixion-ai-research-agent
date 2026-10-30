"""Non-agentic baseline: same Gemini model, no tools. Compare against the agent.

Usage:  python -m evaluation.baseline "your question"
"""
import os
import sys
import time

from dotenv import load_dotenv
from google import genai

from app import config

load_dotenv()


def baseline_answer(question: str) -> tuple[str, float]:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    t0 = time.perf_counter()
    resp = client.models.generate_content(
        model=config.gemini_model(),
        contents=f"Answer concisely, with sources and a confidence level:\n{question}",
    )
    return resp.text or "", round(time.perf_counter() - t0, 1)


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Compare the top 3 open-source vector databases for RAG."
    text, secs = baseline_answer(q)
    print(f"[baseline: {secs}s, no tools, URLs below are UNVERIFIED]\n{text}")
