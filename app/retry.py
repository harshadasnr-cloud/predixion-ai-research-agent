"""Retry with exponential backoff, for transient errors only."""
import logging
import random
import time

from app import config

logger = logging.getLogger(__name__)

TRANSIENT_CODES = {408, 429, 500, 502, 503, 504}


def is_transient(exc: Exception) -> bool:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code in TRANSIENT_CODES
    name = type(exc).__name__.lower()
    return any(key in name for key in ("timeout", "connect", "unavailable"))


def call_with_retry(fn, *, attempts=None, base_delay=None, sleep=None):
    attempts = attempts or config.RETRY_ATTEMPTS
    base_delay = config.RETRY_BASE_DELAY if base_delay is None else base_delay
    sleep = sleep or time.sleep

    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == attempts or not is_transient(exc):
                raise
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            logger.warning(
                "Transient %s (attempt %s/%s); retrying in %.1fs.",
                type(exc).__name__, attempt, attempts, delay,
            )
            sleep(delay)
