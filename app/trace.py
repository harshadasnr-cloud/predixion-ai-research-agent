"""Per-run trace: step timings, counters, token usage -> JSONL file."""
import json
import os
import threading
import time
import uuid
from collections import defaultdict
from contextlib import contextmanager


class Trace:
    def __init__(self, question: str):
        self.run_id = uuid.uuid4().hex[:12]
        self.question = question
        self.started = time.perf_counter()
        self.steps: list[dict] = []
        self.counters: dict[str, int] = defaultdict(int)
        self.flags: dict[str, object] = {}
        self._lock = threading.Lock()

    def inc(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self.counters[name] += amount

    @contextmanager
    def step(self, name: str, **info):
        record = {"step": name, **info}
        t0 = time.perf_counter()
        try:
            yield record
        except Exception as exc:
            record["status"] = "error"
            record["error"] = type(exc).__name__
            raise
        else:
            record.setdefault("status", "ok")
        finally:
            record["duration_s"] = round(time.perf_counter() - t0, 3)
            self.steps.append(record)

    def add_usage(self, response) -> None:
        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            return
        self.inc("prompt_tokens", int(getattr(usage, "prompt_token_count", 0) or 0))
        self.inc("output_tokens", int(getattr(usage, "candidates_token_count", 0) or 0))

    def metadata(self) -> dict:
        return {
            "run_id": self.run_id,
            "planner_mode": self.flags.get("planner_mode", "fallback"),
            "searches": self.counters["searches"],
            "fetches_ok": self.counters["fetch_ok"],
            "fetches_failed": self.counters["fetch_failed"],
            "tool_errors": self.counters["tool_errors"],
            "reformulated": bool(self.flags.get("reformulated", False)),
            "injection_flagged": self.counters["injection_flagged"],
            "used_fallback": bool(self.flags.get("used_fallback", False)),
            "latency_s": round(time.perf_counter() - self.started, 2),
            "prompt_tokens": self.counters["prompt_tokens"],
            "output_tokens": self.counters["output_tokens"],
        }

    def flush(self) -> None:
        path = os.getenv("TRACE_FILE", "logs/traces.jsonl")
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(
                    {"question": self.question, **self.metadata(), "steps": self.steps},
                    ensure_ascii=False,
                ) + "\n")
        except OSError:
            pass  # tracing must never break a run
