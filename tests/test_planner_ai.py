
import json

from app import planner


def test_missing_gemini_key_uses_fallback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    plan = planner.create_research_plan("How does RAG work?")

    assert plan.planner_mode == "fallback"
    assert plan.question == "How does RAG work?"


def test_gemini_plan_is_validated(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    payload = {
        "question": "How does RAG work?",
        "sub_questions": ["How does retrieval support generation?"],
        "steps": [
            {
                "task": "Search for RAG research",
                "tool": "web_search",
                "purpose": "Find relevant technical evidence",
            },
            {
                "task": "Inspect a relevant source",
                "tool": "web_fetch",
                "purpose": "Review supporting evidence",
            },
        ],
    }

    class FakeResponse:
        text = json.dumps(payload)

    class FakeModels:
        def generate_content(self, **kwargs):
            assert kwargs["config"]["response_mime_type"] == "application/json"
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(planner.genai, "Client", FakeClient)

    plan = planner.create_research_plan("How does RAG work?")

    assert plan.planner_mode == "llm"
    assert len(plan.steps) == 2
    assert {step.tool for step in plan.steps} == {
        "web_search",
        "web_fetch",
    }


def test_invalid_gemini_output_uses_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class FakeResponse:
        text = '{"question":"test","sub_questions":[],"steps":[]}'

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(planner.genai, "Client", FakeClient)

    plan = planner.create_research_plan("Explain AI research agents")

    assert plan.planner_mode == "fallback"
    assert plan.question == "Explain AI research agents"
