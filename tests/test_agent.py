
import json

import pytest

from app import agent
from app.models import ResearchReport
from app.planner import create_fallback_plan


def test_short_question_is_rejected():
    with pytest.raises(ValueError, match="at least 3 characters"):
        agent.run_research("Hi")


def test_no_evidence_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(
        agent,
        "create_research_plan",
        create_fallback_plan,
    )
    monkeypatch.setattr(agent, "search_web", lambda *args, **kwargs: [])

    with pytest.raises(RuntimeError, match="could not collect"):
        agent.run_research("How does RAG work?")


def test_research_workflow_with_mocked_apis(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.8-flash")

    plan = create_fallback_plan("How does RAG work?")
    monkeypatch.setattr(agent, "create_research_plan", lambda question: plan)

    monkeypatch.setattr(
        agent,
        "search_web",
        lambda *args, **kwargs: [
            {
                "title": "RAG Research Overview",
                "url": "https://example.com/rag",
                "content": "RAG retrieves external information to support generation.",
                "score": 0.95,
            }
        ],
    )

    monkeypatch.setattr(
        agent,
        "fetch_webpage",
        lambda url: {
            "title": "RAG Research Overview",
            "content": "RAG retrieves external information to support generation.",
        },
    )

    payload = {
        "user_question": "How does RAG work?",
        "short_answer": (
            "RAG retrieves external evidence to support generated answers."
        ),
        "key_findings": [
            {
                "finding": "RAG retrieves external information.",
                "source_urls": ["https://example.com/rag"],
            }
        ],
        "sources": [
            {
                "title": "RAG Research Overview",
                "url": "https://example.com/rag",
                "summary": "An illustrative source used by this test.",
                "source_type": "research",
            }
        ],
        "confidence_level": "medium",
        "limitations_or_assumptions": [
            "The test uses an illustrative source."
        ],
        "suggested_next_steps": [
            "Verify the claim against primary research."
        ],
    }

    class FakeResponse:
        text = json.dumps(payload)

    class FakeModels:
        def generate_content(self, **kwargs):
            assert kwargs["model"] == "gemini-3.8-flash"
            assert kwargs["config"]["response_mime_type"] == "application/json"
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == "test-key"
            self.models = FakeModels()

    monkeypatch.setattr(agent.genai, "Client", FakeClient)

    report = agent.run_research("How does RAG work?")

    assert isinstance(report, ResearchReport)
    assert report.confidence_level == "medium"
    assert len(report.key_findings) == 1
    assert str(report.sources[0].url) == "https://example.com/rag"


def test_rejects_unsupported_source_url(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    plan = create_fallback_plan("Explain AI research agents")
    monkeypatch.setattr(agent, "create_research_plan", lambda question: plan)

    monkeypatch.setattr(
        agent,
        "search_web",
        lambda *args, **kwargs: [
            {
                "title": "Example Research",
                "url": "https://example.com/research",
                "content": "An illustrative research result.",
                "score": 0.9,
            }
        ],
    )

    payload = {
        "user_question": "Explain AI research agents",
        "short_answer": "Research agents gather and synthesize information.",
        "key_findings": [
            {
                "finding": "Agents can use tools to gather evidence.",
                "source_urls": ["https://example.com/research"],
            }
        ],
        "sources": [
            {
                "title": "Unsupported Source",
                "url": "https://not-in-evidence.example/",
                "summary": "This URL was never returned by the search tool.",
                "source_type": "other",
            }
        ],
        "confidence_level": "low",
        "limitations_or_assumptions": [],
        "suggested_next_steps": [],
    }

    class FakeResponse:
        text = json.dumps(payload)

    class FakeModels:
        def generate_content(self, **kwargs):
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs):
            self.models = FakeModels()

    monkeypatch.setattr(agent.genai, "Client", FakeClient)

    with pytest.raises(RuntimeError, match="failed validation"):
        agent.run_research("Explain AI research agents")
