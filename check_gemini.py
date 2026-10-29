
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not api_key:
    print("Gemini: FAIL — GEMINI_API_KEY is missing from .env")
    raise SystemExit(1)

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(timeout=20000),
)

for attempt in range(1, 3):
    try:
        print(f"Testing Gemini (attempt {attempt}/2)...")

        response = client.models.generate_content(
            model=model,
            contents="Reply with exactly: OK",
        )

        if response.text:
            print(f"Gemini: PASS — API request succeeded using {model}.")
            break

        print("Gemini: FAIL — The API returned no text.")
        raise SystemExit(1)

    except Exception as exc:
        print(f"Attempt {attempt} failed: {type(exc).__name__}")

        if attempt == 2:
            print(
                "Gemini could not complete the request after two attempts. "
                "Try again later if the service is slow."
            )
            raise SystemExit(1)

        time.sleep(2)
