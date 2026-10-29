# Evaluation Report

## 1. Objective

Evaluate the Predixion AI Research Agent for research quality, structured output, source handling, reliability, and failure handling.

## 2. Automated Test Results

- Total automated tests: 21
- Passed: 21
- Failed: 0

The automated tests cover report schema validation, web fetching, search functionality, planner behavior, AI planner behavior, and agent orchestration.

Note: These tests include mocked dependencies. Passing tests does not guarantee that every external API or website will work reliably.

## 3. Evaluation Scenarios

| ID | Scenario | Expected Outcome | Observed Result | Status |
|---|---|---|---|---|
| E1 | Research a healthcare AI topic | Produce a structured report with findings and sources | A live run produced a validated report with findings, a source, confidence, limitations, and next steps | Passed |
| E2 | Validate report structure | Reject invalid or incomplete report data | Automated model validation tests passed | Passed |
| E3 | Search tool behavior | Validate and normalize search results | Search tests passed | Passed |
| E4 | Web-fetch failures | Handle inaccessible or unsupported webpages without crashing the workflow unnecessarily | Some webpage fetches failed during the live run; the agent continued with available evidence | Passed with limitations |
| E5 | Planner behavior | Produce a research plan or use a fallback when planning fails | Planner tests passed | Passed |
| E6 | AI planner behavior | Handle AI planner responses and failure cases | AI planner tests passed | Passed |
| E7 | Agent orchestration | Coordinate tools and return a report | Agent tests passed; one live end-to-end run completed successfully | Passed |

## 4. Live Run Observations

Research question:
"What are the latest applications of AI agents in healthcare?"

Observed:
- The planner completed successfully using Gemini.
- The agent performed web search and attempted to fetch source pages.
- Some webpage fetches failed.
- The synthesis step completed and returned a validated research report.
- The report included a short answer, key findings, source information, confidence level, limitations, and suggested next steps.

The observed report used a healthcare AI news compilation as its source. Its findings should be independently checked against primary research and official sources before being treated as authoritative.

## 5. Known Limitations

- Website accessibility and external API availability can affect results.
- Search-result citations do not independently prove that every claim is supported by the cited source.
- Source quality and factual accuracy still require review.
- External model responses may vary between runs.
- More live tests across different research topics are needed.

## 6. Conclusion

The current implementation passes all 21 automated tests and has completed a live research run. The agent demonstrates the core research workflow, structured report validation, and partial resilience to webpage-fetch failures. Further evaluation of citation support, source diversity, and repeated live runs would strengthen confidence in production readiness.
