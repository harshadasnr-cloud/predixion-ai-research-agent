"""Single place for every tunable. Change budgets here, not in the logic."""
import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL_DEFAULT = "gemini-flash-lite-latest"


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", GEMINI_MODEL_DEFAULT)


# Tool budgets (cost / latency control)
MAX_SEARCHES = 4          # 1 slot is reserved for an adaptive reformulated search
MAX_FETCHES = 4
MAX_SOURCES_IN_PACK = 8
MAX_EVIDENCE_CHARS = 12_000

# Source filtering
MIN_SCORE = 0.25
MAX_PER_DOMAIN = 2

# Timeouts (ms for Gemini)
PLANNER_TIMEOUT_MS = 15_000
SYNTH_TIMEOUT_MS = 30_000

# Retry
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0
