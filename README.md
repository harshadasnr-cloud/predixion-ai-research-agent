# Predixion AI Research Agent

A production-oriented AI research agent that plans research tasks, uses external tools, filters retrieved evidence, and produces structured, source-backed answers.

## Project Status

Initial project setup completed. Agent implementation and evaluation are in progress.

## Planned Architecture

1. Accept a research question.
2. Generate a structured research plan.
3. Select and execute research tools.
4. Retrieve and filter evidence.
5. Synthesize a structured answer with sources.
6. Validate the response and report limitations.

## Technology Stack

- Python 3.12
- OpenAI Python SDK
- Tavily Search API
- Pydantic
- Requests and Beautiful Soup
- Pytest

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Configure API keys in a local `.env` file.
4. Run the application using the instructions added as implementation progresses.

## Reliability and Safety

The planned system will include bounded tool execution, error handling, evidence filtering, structured output validation, and safeguards against prompt injection.

## Evaluation

At least five research and failure-case queries will be evaluated. Results will be documented after tests have actually been run.

## Known Limitations

Implementation, evaluation results, and production-readiness status will be documented as the project develops.

## Future Improvements

Potential improvements include caching, an evaluator step, asynchronous tool execution, and comparison with a non-agentic baseline.