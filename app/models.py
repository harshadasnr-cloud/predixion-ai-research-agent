
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Source(BaseModel):
    """A source used to support the research answer."""

    title: str = Field(min_length=1, max_length=300)
    url: HttpUrl
    summary: str = Field(min_length=1, max_length=1500)
    source_type: Literal["official", "research", "news", "other"] = "other"


class KeyFinding(BaseModel):
    """An individual research finding."""

    finding: str = Field(min_length=1, max_length=1500)
    source_urls: list[HttpUrl] = Field(default_factory=list)


class ResearchReport(BaseModel):
    """The validated final response returned by the research agent."""

    user_question: str = Field(min_length=3, max_length=2000)
    short_answer: str = Field(min_length=1, max_length=2000)
    key_findings: list[KeyFinding] = Field(min_length=1, max_length=10)
    sources: list[Source] = Field(min_length=1, max_length=15)
    confidence_level: Literal["high", "medium", "low"]
    limitations_or_assumptions: list[str] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)

    @field_validator("user_question", "short_answer")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be blank.")
        return value.strip()
