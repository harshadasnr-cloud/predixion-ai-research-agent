
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ResearchStep(BaseModel):
    """One step in the research workflow."""

    task: str = Field(min_length=5, max_length=500)
    tool: Literal["web_search", "web_fetch"]
    purpose: str = Field(min_length=5, max_length=300)


class ResearchPlan(BaseModel):
    """A validated plan created before research begins."""

    question: str = Field(min_length=3, max_length=2000)
    sub_questions: list[str] = Field(min_length=1, max_length=5)
    steps: list[ResearchStep] = Field(min_length=1, max_length=8)

    @field_validator("question")
    @classmethod
    def reject_blank_question(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Question cannot be blank.")
        return value.strip()

    @field_validator("sub_questions")
    @classmethod
    def validate_sub_questions(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("Sub-questions cannot be blank.")
        return cleaned


def create_fallback_plan(question: str) -> ResearchPlan:
    """Create a predictable plan when an LLM planner is unavailable.

    This fallback is transparent and does not claim that research has
    already been performed.
    """
    cleaned_question = question.strip()

    if len(cleaned_question) < 3:
        raise ValueError("Please enter a question with at least 3 characters.")

    return ResearchPlan(
        question=cleaned_question,
        sub_questions=[
            f"What are the main facts relevant to: {cleaned_question}?",
            "Which reliable sources support the key facts?",
            "What uncertainties or limitations should be reported?",
        ],
        steps=[
            ResearchStep(
                task=f"Search the web for reliable information about: {cleaned_question}",
                tool="web_search",
                purpose="Find relevant sources and evidence for the question.",
            ),
            ResearchStep(
                task="Open the most relevant search results and inspect their content.",
                tool="web_fetch",
                purpose="Check source details and collect supporting evidence.",
            ),
        ],
    )
