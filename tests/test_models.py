
import pytest
from pydantic import ValidationError

from app.models import ResearchReport


def test_valid_report_is_accepted():
    report = ResearchReport(
        user_question="What is retrieval-augmented generation?",
        short_answer="RAG combines information retrieval with language generation.",
        key_findings=[
            {
                "finding": "RAG retrieves relevant external information.",
                "source_urls": ["https://example.com/rag"],
            }
        ],
        sources=[
            {
                "title": "RAG Overview",
                "url": "https://example.com/rag",
                "summary": "An illustrative overview of RAG.",
                "source_type": "research",
            }
        ],
        confidence_level="medium",
        limitations_or_assumptions=[
            "The example source is illustrative."
        ],
        suggested_next_steps=[
            "Verify findings against primary research."
        ],
    )

    assert report.confidence_level == "medium"
    assert len(report.key_findings) == 1
    assert len(report.sources) == 1


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValidationError):
        ResearchReport(
            user_question="What is RAG?",
            short_answer="RAG retrieves external information.",
            key_findings=[
                {"finding": "Retrieves relevant information."}
            ],
            sources=[
                {
                    "title": "Example",
                    "url": "https://example.com",
                    "summary": "Illustrative source.",
                }
            ],
            confidence_level="certain",
        )


def test_blank_question_is_rejected():
    with pytest.raises(ValidationError):
        ResearchReport(
            user_question="   ",
            short_answer="An example answer.",
            key_findings=[
                {"finding": "An example finding."}
            ],
            sources=[
                {
                    "title": "Example",
                    "url": "https://example.com",
                    "summary": "Illustrative source.",
                }
            ],
            confidence_level="low",
        )
