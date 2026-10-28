
# Predixion AI Research Agent

A production-oriented AI research agent built for the Predixion AI Platform Engineering Internship assignment.

## Objective

Build an agent that plans research tasks, selects tools, retrieves and filters evidence, and produces structured, source-backed answers.

## Planned Architecture

1. Accept a research question.
2. Generate a structured research plan.
3. Orchestrate web search and webpage retrieval.
4. Filter irrelevant, duplicate, and low-quality evidence.
5. Synthesize an answer grounded in retrieved evidence.
6. Validate the final response schema.
7. Report confidence, assumptions, limitations, and next steps.

## Technology Stack

- Python
- OpenAI API
- Tavily Search
- Pydantic
- Requests and BeautifulSoup
- Pytest

## Project Structure

- `app/` - Agent orchestration and application logic
- `app/tools/` - Research tools
- `tests/` - Automated tests
- `evaluation/` - Evaluation queries and results
- `sample_outputs/` - Sample reports

## Setup

Setup instructions will be finalized after implementation and testing.

## Evaluation

The evaluation will cover at least five research queries, including successful cases and failure or edge cases.

## Limitations

To be documented after implementation and testing.

## Future Improvements

Potential improvements include caching, asynchronous tool execution, and a separate evaluation or judge step.
