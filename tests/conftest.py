import pytest


@pytest.fixture(autouse=True)
def _isolate(monkeypatch, tmp_path):
    monkeypatch.setenv("TRACE_FILE", str(tmp_path / "trace.jsonl"))
    monkeypatch.setattr("time.sleep", lambda *_: None)
