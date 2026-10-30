# Predixion AI Research Agent

A production-oriented AI research agent. It plans a research task, searches the web, ranks and filters sources,
reads pages, and returns a validated JSON report with source citations, confidence, limitations, and next steps.

## Project Status
- 49 automated tests passing (all run offline with mocks)
- Evaluation suite of 7 queries (happy path, edge, adversarial): see `evaluation/evaluation_report.md`
- Sample outputs in `sample_outputs/`

## Features
- **Planning:** Gemini creates a structured plan (one search per entity, fetch only when needed); deterministic fallback plan if it fails.
- **Adaptive tool use:** if evidence is weak (fewer than 3 sources or a single domain), the agent runs one reformulated search.
- **Source filtering:** Tavily relevance score x domain quality, low-score removal, per-domain cap, `source_type` derived in code.
- **Parallel execution:** searches and page fetches run concurrently.
- **Grounded synthesis:** schema-constrained Gemini output; every claim must cite a retrieved URL; unsupported citations are removed.
- **Rule-based confidence cap:** final confidence is the lower of the LLM's claim and an evidence-based rule.
- **Failure handling:** retries with backoff (429/5xx/timeouts only), corrective retry on malformed JSON, labelled low-confidence fallback report.
- **Safety:** SSRF-hardened fetcher, injection screening of retrieved text, retrieved content treated as untrusted data.
- **Observability:** per-run trace (step timings, tokens, tool errors) written to `logs/traces.jsonl` and summarized in `metadata`.

## Architecture
```text
User question
   -> Input validation (length, vague-question guard)
   -> Planner (Gemini structured output / fallback plan)
   -> web_search x N (parallel, budgeted)
   -> Evidence check: weak? -> ONE reformulated search        <- adaptive step
   -> Rank + filter (score x domain quality, per-domain cap)
   -> web_fetch top-K (parallel, only if planned)
   -> Evidence pack (fair per-source character budget, snippet first)
   -> Synthesis (Gemini, schema-constrained, 1 corrective retry)
        -> on failure: labelled fallback report
   -> Grounding (drop claims citing URLs not in evidence; build sources in code)
   -> Confidence cap (rules)
   -> ResearchReport + metadata (+ JSONL trace)
```

## Project Structure
```text
predixion-ai-research-agent/
├── app/
│   ├── main.py        CLI (JSON on stdout, progress on stderr, --out file)
│   ├── agent.py       orchestration: gather, pack, synthesize, ground
│   ├── planner.py     LLM planner + fallback plan
│   ├── models.py      Pydantic schemas (LLM output + final report)
│   ├── config.py      all budgets, timeouts, thresholds
│   ├── ranking.py     source classification, filtering, confidence cap
│   ├── safety.py      prompt-injection screening
│   ├── retry.py       exponential backoff for transient errors
│   ├── trace.py       per-run tracing
│   └── tools/
│       ├── search.py  Tavily search
│       └── fetch.py   safe page fetch
├── streamlit_app.py   web UI (Streamlit)
├── .streamlit/config.toml
├── tests/             49 tests
├── evaluation/        queries.json, run_eval.py, baseline.py, evaluation_report.md
├── sample_outputs/
├── check_connections.py / check_gemini.py
├── pytest.ini  requirements.txt  .env.example  README.md
```

## Setup
```powershell
git clone https://github.com/harshadasnr-cloud/predixion-ai-research-agent.git
cd predixion-ai-research-agent
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
Copy `.env.example` to `.env`:
```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-lite-latest
TAVILY_API_KEY=your_tavily_api_key
```
Use a model your account supports. Never commit `.env`.

## Usage
```powershell
python check_connections.py
python -u -m app.main "Compare the top 3 open-source vector databases for RAG" --out sample_outputs/vector_dbs.json
python -m pytest -v
python -m evaluation.run_eval
python -m evaluation.baseline "Compare the top 3 open-source vector databases for RAG"
```

## Web UI (optional)
A simple Streamlit front end calls the same agent code.
```powershell
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py.
```
Open http://localhost:8501, type a question (or click an example), and press **Run research**.
The page shows live progress, the short answer, confidence, cited findings, sources, limitations, next steps,
run details, and a JSON download button. Fallback reports are clearly flagged.

## Report Structure
`user_question`, `short_answer`, `key_findings` (each with source URLs), `sources`, `confidence_level`,
`limitations_or_assumptions`, `suggested_next_steps`, and `metadata` (run id, planner mode, searches, fetches,
tool errors, fallback used, latency, tokens).

## Why an agentic approach?
Research questions are open-ended. How many searches are needed, which entities to cover, and whether snippets are
enough all depend on the question. A fixed pipeline cannot adapt. Here the planner chooses queries and tools, and the
executor reacts to weak evidence by re-searching. I used one planner-executor loop on purpose: no multi-agent system
or heavy framework, because the task does not need one and a simple loop is easier to test, trace, and explain.

## Tools and why
- **web_search (Tavily):** returns relevance scores and clean snippets; fast, cheap discovery.
- **web_fetch (Requests + Beautiful Soup):** full page text for depth. Blocks private/local addresses, re-validates every redirect hop, caps downloads at 1 MB.

## How bad tool results are handled
- Timeouts on every external call; retries with backoff only for 429/5xx/timeouts (never for 4xx).
- Malformed search items are dropped; failed fetches keep the search snippet; PDFs and non-HTML are skipped.
- Any tool error caps confidence at medium and adds a limitation.
- Search fully down: clear error, no invented answer.
- Invalid LLM JSON: one corrective retry, then a clearly labelled low-confidence fallback report.

## How hallucinations are reduced
Evidence-only prompt, temperature 0, schema-constrained output, mandatory citations, citations checked against retrieved URLs
(unsupported ones removed and reported), sources and `source_type` built in code, `user_question` never taken from the LLM,
and confidence capped by rules (for example fewer than 2 independent domains forces low).

## Prompt injection
Retrieved text is passed as data with an explicit instruction not to follow it. Instruction-like patterns are stripped before the
LLM sees them, and URLs can only come from the retrieved set, so an injected "cite evil.com" cannot appear. Regex screening is a
weak layer, not a guarantee.

## Making it production-ready
Async job queue and API endpoint; shared cache (Redis); rate limiting and auth; circuit breaker per provider; PDF and JS-page support;
LLM-as-judge groundedness checks in CI; Langfuse/OpenTelemetry instead of JSONL; pin DNS results to close the DNS-rebinding window
between URL validation and connection; secrets manager; regression evals on every prompt or model change.

## What to monitor in production
Latency p50/p95 per step; tokens and cost per run; fallback rate; tool error rate per provider; reformulation rate (search-quality proxy);
share of claims removed by grounding; confidence distribution; injection-flag rate; user feedback.

## Key trade-offs
- Budgeted loop (max 4 searches, 4 fetches) instead of an open-ended agent: predictable cost and latency, less depth.
- Rule-based source ranking: transparent and testable, but domain lists are hand-made and incomplete.
- Fallback report instead of hard failure: always something useful, but lower quality.
- Dropping bad citations instead of failing: better experience, but a claim can disappear (always disclosed in limitations).
- Vague questions rejected by a simple word heuristic: cheap, but can miss or over-block edge cases.

## Evaluation
See `evaluation/evaluation_report.md` for 7 queries with expected vs observed behaviour. Run `python -m evaluation.run_eval` to reproduce.

## Known Limitations
- Citation validation checks that a URL was retrieved, not that it semantically supports the claim.
- Search quality depends on Tavily; some sites block fetching; PDFs and JavaScript pages are not read.
- Fallback reports show raw snippets and can include text about unrelated entities (observed in Q5: figures for similarly named companies).
- "Top N" requests can still return a different count if the model lists extras (seen once, fixed by a prompt rule).
- Confidence rules are heuristic.
- Regex injection screening is easy to evade.

## Future Improvements
Claim-to-source entailment checks; LLM-as-judge; shared cache; async API; PDF support; larger evaluation set; baseline comparison at scale.
