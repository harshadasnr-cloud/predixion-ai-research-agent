from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ---------- What we ask Gemini to return (plain types: schema-friendly) ----------
class LLMFinding(BaseModel):
    finding: str
    source_urls: list[str]


class LLMSource(BaseModel):
    url: str
    summary: str


class LLMReport(BaseModel):
    short_answer: str
    key_findings: list[LLMFinding]
    sources: list[LLMSource]
    confidence_level: Literal["high", "medium", "low"]
    limitations_or_assumptions: list[str]
    suggested_next_steps: list[str]


# ---------- What we return to the user (strict, validated) ----------
class Source(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    url: HttpUrl
    summary: str = Field(min_length=1, max_length=1500)
    source_type: Literal["official", "research", "news", "other"] = "other"


class KeyFinding(BaseModel):
    finding: str = Field(min_length=1, max_length=1500)
    source_urls: list[HttpUrl] = Field(min_length=1)  # every claim must be cited


class RunMetadata(BaseModel):
    run_id: str
    planner_mode: str
    searches: int = 0
    fetches_ok: int = 0
    fetches_failed: int = 0
    tool_errors: int = 0
    reformulated: bool = False
    injection_flagged: int = 0
    used_fallback: bool = False
    latency_s: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0


class ResearchReport(BaseModel):
    user_question: str = Field(min_length=3, max_length=2000)
    short_answer: str = Field(min_length=1, max_length=2000)
    key_findings: list[KeyFinding] = Field(min_length=1, max_length=10)
    sources: list[Source] = Field(min_length=1, max_length=15)
    confidence_level: Literal["high", "medium", "low"]
    limitations_or_assumptions: list[str] = Field(default_factory=list)
    suggested_next_steps: list[str] = Field(default_factory=list)
    metadata: RunMetadata | None = None

    @field_validator("user_question", "short_answer")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("This field cannot be blank.")
        return value.strip()
