import json


def fake_gemini(monkeypatch, agent, responses):
    """responses: list of payload dicts / raw strings / Exceptions, consumed in order."""
    queue = list(responses)

    class FakeResponse:
        def __init__(self, text):
            self.text = text

    class FakeModels:
        def generate_content(self, **kwargs):
            item = queue.pop(0) if len(queue) > 1 else queue[0]
            if isinstance(item, Exception):
                raise item
            return FakeResponse(item if isinstance(item, str) else json.dumps(item))

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(agent.genai, "Client", FakeClient)


def good_payload(url="https://example.com/rag", **over):
    payload = {
        "short_answer": "RAG retrieves external evidence to support generation.",
        "key_findings": [{"finding": "RAG retrieves external information.", "source_urls": [url]}],
        "sources": [{"url": url, "summary": "Overview of RAG."}],
        "confidence_level": "high",
        "limitations_or_assumptions": [],
        "suggested_next_steps": [],
    }
    payload.update(over)
    return payload
