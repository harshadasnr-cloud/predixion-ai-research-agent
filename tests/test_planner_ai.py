
import json

from app import planner


def test_missing_openai_key_uses_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    plan = planner.create_research_plan("How does RAG work?")

    assert plan.planner_mode == "fallback"
    assert plan.question == "How does RAG work?"


def test_openai_plan_is_validated(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    response_payload = {
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
                "purpose": "Review source details and supporting evidence",
            },
        ],
    }

    class FakeMessage:
        content = json.dumps(response_payload)

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["response_format"] == {"type": "json_object"}
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type(
                "Chat",
                (),
                {"completions": FakeCompletions()},
            )()

    monkeypatch.setattr(planner, "OpenAI", FakeClient)

    plan = planner.create_research_plan("How does RAG work?")

    assert plan.planner_mode == "llm"
    assert len(plan.steps) == 2
    assert {step.tool for step in plan.steps} == {
        "web_search",
        "web_fetch",
    }


def test_invalid_model_output_uses_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeMessage:
        content = '{"question":"test","sub_questions":[],"steps":[]}'

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type(
                "Chat",
                (),
                {"completions": FakeCompletions()},
            )()

    monkeypatch.setattr(planner, "OpenAI", FakeClient)

    plan = planner.create_research_plan("Explain AI research agents")

    assert plan.planner_mode == "fallback"
    assert plan.question == "Explain AI research agents"
