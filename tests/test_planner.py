
import pytest
from pydantic import ValidationError

from app.planner import (
    ResearchPlan,
    ResearchStep,
    create_fallback_plan,
)


def test_fallback_plan_contains_both_tools():
    plan = create_fallback_plan("How does retrieval-augmented generation work?")

    assert isinstance(plan, ResearchPlan)
    assert plan.question.startswith("How does")
    assert len(plan.sub_questions) >= 1

    selected_tools = {step.tool for step in plan.steps}
    assert selected_tools == {"web_search", "web_fetch"}


def test_blank_question_is_rejected():
    with pytest.raises(ValueError):
        create_fallback_plan("  ")


def test_invalid_tool_is_rejected():
    with pytest.raises(ValidationError):
        ResearchStep(
            task="Search for relevant evidence",
            tool="database",
            purpose="Find information for the report",
        )
