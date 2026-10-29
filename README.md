
# Predixion AI Research Agent

A production-oriented AI research agent that plans research tasks, searches the web, collects evidence, and generates structured research reports with source citations, confidence levels, limitations, and suggested next steps.

## Project Status

**Core implementation completed; automated tests passing.**

- 21 automated tests passing
- LLM-based research planning using Google Gemini
- Web search using Tavily
- Webpage retrieval using Requests and Beautiful Soup
- Structured report validation using Pydantic
- Fallback planning and report generation for selected failures
- Evidence-based citation validation
- Logging, progress updates, and bounded research execution

Some webpage fetches and external API calls may fail. The agent handles selected failures gracefully and reports limitations when evidence collection is incomplete.

## Features

- **Research planning:** Generates a structured plan from the user's question.
- **Tool orchestration:** Executes bounded web-search and webpage-fetch operations.
- **Evidence collection:** Collects and limits retrieved evidence before synthesis.
- **AI synthesis:** Uses Gemini to generate a structured research report.
- **Output validation:** Validates report fields and checks that cited URLs belong to collected evidence.
- **Fallback handling:** Uses a fallback plan when AI planning fails and can produce a clearly labelled, low-confidence report when Gemini synthesis is unavailable.
- **Safety controls:** Restricts webpage fetching to supported HTTP/HTTPS URLs and treats retrieved webpage content as untrusted data.
- **Progress logging:** Reports research stages and selected failures.

## Architecture

```text
User Research Question
        |
        v
Input Validation
        |
        v
Research Planner (Gemini / Fallback)
        |
        v
Research Orchestrator
        |
        +---------------------+
        |                     |
        v                     v
   Tavily Search        Webpage Fetch
        |                     |
        +----------+----------+
                   |
                   v
            Evidence Collection
                   |
                   v
           Evidence Size Limits
                   |
                   v
          Gemini Report Synthesis
                   |
             +-----+-----+
             |           |
             v           v
       Schema Check   Fallback Report
             |           |
             +-----+-----+
                   |
                   v
          Citation Validation
                   |
                   v
          Structured JSON Report
```

## Technology Stack

- Python 3.12
- Google Gemini API
- Google GenAI Python SDK
- Tavily Search API
- Pydantic
- Requests
- Beautiful Soup
- python-dotenv
- Pytest

## Project Structure

```text
predixion-ai-research-agent/
├── app/
│   ├── main.py
│   ├── agent.py
│   ├── planner.py
│   ├── models.py
│   └── tools/
│       ├── search.py
│       └── fetch.py
├── tests/
│   ├── test_agent.py
│   ├── test_fetch.py
│   ├── test_models.py
│   ├── test_planner.py
│   ├── test_planner_ai.py
│   └── test_search.py
├── evaluation/
├── sample_outputs/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.12
- A Google Gemini API key with access to a supported text-generation model
- A Tavily API key
- Internet access

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/harshadasnr-cloud/predixion-ai-research-agent.git
cd predixion-ai-research-agent
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your own API keys.

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-lite-latest
TAVILY_API_KEY=your_tavily_api_key
```

Use a model supported by your API account. The model shown above was used successfully in the development environment; availability may vary.

**Security:** Never commit `.env` or expose API keys in logs, screenshots, or source control.

### 5. Run the research agent

```powershell
python -u -m app.main "What are the latest applications of AI agents in healthcare?"
```

The agent displays progress updates and prints the structured research report as JSON.

## Report Structure

The report contains:

- `user_question`: The original research question
- `short_answer`: A concise response
- `key_findings`: Findings with associated source URLs
- `sources`: Source titles, URLs, summaries, and source types
- `confidence_level`: High, medium, or low
- `limitations_or_assumptions`: Known limitations and assumptions
- `suggested_next_steps`: Recommended follow-up actions

## Testing

Run the automated test suite:

```powershell
python -m pytest -v
```

**Latest recorded result:** 21 tests passed.

The tests cover input validation, research orchestration, report models, planner behavior, search-result normalization, webpage-fetch safety, and citation validation. External API behavior is primarily tested using mocks; passing tests do not guarantee that external services are always available.

## Evaluation

The evaluation should include at least five research questions and failure scenarios. Record the expected behavior, observed behavior, evidence quality, citation validity, and whether the run completed successfully.

Keep evaluation results in the `evaluation/` directory. Include actual observed results rather than assumed outcomes.

## Reliability and Safety

- Bounded search and fetch operations
- Request timeouts and error handling in external tools
- Structured output validation
- Citation checks against collected evidence
- URL validation to reduce unsafe webpage-fetching requests
- Explicit limitations and reduced confidence when research steps fail
- Fallback behavior for selected AI-provider failures

These controls improve robustness but do not guarantee that every source is reliable or that every generated claim is correct. Sources should be independently verified before important decisions.

## Known Limitations

- External AI and search services may be unavailable, rate-limited, or slow.
- Some websites block automated fetching or return unsupported content.
- Search snippets may provide incomplete context when full-page fetching fails.
- Citation validation checks whether a URL was collected; it does not independently prove that a source supports the associated claim.
- Fallback reports contain retrieved evidence snippets and are not equivalent to full AI synthesis.
- Research quality depends on the relevance, accuracy, and diversity of retrieved sources.

## Future Improvements

- Add retry policies with exponential backoff for transient API failures.
- Improve webpage-fetch diagnostics and source diversity.
- Add automated citation-to-claim support checks.
- Expand evaluation across research domains and failure scenarios.
- Measure latency, cost, and research quality.
- Add caching and asynchronous tool execution where appropriate.
- Compare agent performance against a non-agentic baseline.

## License

Add a license before distributing the project publicly if you intend to make its reuse terms explicit.
