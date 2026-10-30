"""Simple web UI for the research agent.

Run from the project root:
    streamlit run streamlit_app.py
"""
import json
import os

import streamlit as st
from dotenv import load_dotenv

from app import agent

load_dotenv()

st.set_page_config(page_title="AI Research Agent", page_icon=" ", layout="centered")

EXAMPLES = [
    "Compare the top 3 open-source vector databases for a startup building RAG products.",
    "Find 5 Indian B2B SaaS startups in HR tech and summarize their positioning.",
    "Research the pros and cons of using a multi-agent architecture for customer support automation.",
    "Compare different approaches to adding memory in an AI support agent.",
]
CONFIDENCE_ICON = {"high": "🟢", "medium": "🟡", "low": "🔴"}

for key, default in (("question", ""), ("report", None), ("notice", None)):
    st.session_state.setdefault(key, default)


def set_question(text: str) -> None:
    st.session_state.question = text


def clean(text: str) -> str:
    """Make text safe for st.markdown: no LaTeX from $, no stray newlines."""
    return " ".join(str(text).split()).replace("$", r"\$")


def run_agent(question: str) -> None:
    """Run the agent and stream its progress messages into the page."""
    st.session_state.report = None
    st.session_state.notice = None
    status = st.status("Researching...", expanded=True)

    original_progress = agent.progress
    agent.progress = lambda message: status.write(message)  # live stage updates
    try:
        report = agent.run_research(question)
        st.session_state.report = report.model_dump(mode="json")
        status.update(label="Research complete", state="complete", expanded=False)
    except ValueError as exc:  # bad input, e.g. too short or too vague
        st.session_state.notice = ("warning", str(exc))
        status.update(label="Question needs changes", state="error", expanded=False)
    except RuntimeError as exc:  # no evidence, search down, ...
        st.session_state.notice = ("error", f"Research failed: {exc}")
        status.update(label="Research failed", state="error", expanded=False)
    except Exception:
        st.session_state.notice = ("error", "Unexpected error. Check the terminal logs.")
        status.update(label="Unexpected error", state="error", expanded=False)
    finally:
        agent.progress = original_progress


def render_report(report: dict) -> None:
    level = report["confidence_level"]
    meta = report.get("metadata") or {}

    st.subheader("Short answer")
    st.write(clean(report["short_answer"]))
    st.markdown(f"**Confidence:** {CONFIDENCE_ICON.get(level, '')} {level.upper()}")
    if meta.get("used_fallback"):
        st.warning("Fallback report: the AI synthesis step failed, so this shows raw "
                   "retrieved snippets. Verify the sources before relying on it.")

    numbers = {s["url"]: i for i, s in enumerate(report["sources"], start=1)}

    st.subheader("Key findings")
    for finding in report["key_findings"]:
        links = " ".join(f"[[{numbers[u]}]]({u})" for u in finding["source_urls"] if u in numbers)
        st.markdown(f"- {clean(finding['finding'])}  \n  Sources: {links}")

    st.subheader("Sources")
    for i, source in enumerate(report["sources"], start=1):
        with st.expander(f"[{i}] {clean(source['title'])}  ·  {source['source_type']}"):
            st.markdown(f"[{source['url']}]({source['url']})")
            st.write(clean(source["summary"])[:600])

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Limitations")
        for item in report["limitations_or_assumptions"] or ["None reported."]:
            st.markdown(f"- {clean(item)}")
    with col2:
        st.subheader("Next steps")
        for item in report["suggested_next_steps"] or ["None suggested."]:
            st.markdown(f"- {clean(item)}")

    if meta:
        with st.expander("Run details (trace summary)"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Latency", f"{meta['latency_s']}s")
            c2.metric("Searches / fetches", f"{meta['searches']} / {meta['fetches_ok']}")
            c3.metric("Tokens", meta["prompt_tokens"] + meta["output_tokens"])
            st.json(meta)

    st.download_button("Download report (JSON)", data=json.dumps(report, indent=2),
                       file_name="research_report.json", mime="application/json")


# ------------------------------------------------------------------ page
st.title("🔎 AI Research Agent")
st.caption("Plans, searches the web, filters sources, and returns a cited report "
           "with confidence and limitations.")

with st.sidebar:
    st.header("Setup check")
    st.write(("✅" if os.getenv("GEMINI_API_KEY") else "❌") + " GEMINI_API_KEY")
    st.write(("✅" if os.getenv("TAVILY_API_KEY") else "❌") + " TAVILY_API_KEY")
    st.caption("Keys are read from your local .env file.")
    st.divider()
    st.caption("Each run uses about 2-4 web searches and 1-2 LLM calls, "
               "and takes 10-20 seconds.")

st.text_area("Your research question", key="question", height=100,
             placeholder="e.g. Compare the top 3 open-source vector databases for RAG")

st.caption("Try an example:")
for i, example in enumerate(EXAMPLES):
    st.button(example, key=f"ex{i}", on_click=set_question, args=(example,),
              use_container_width=True)

if st.button("Run research", type="primary"):
    question = st.session_state.question.strip()
    if len(question) < 3:
        st.session_state.report = None
        st.session_state.notice = ("warning", "Please enter a question (at least 3 characters).")
    else:
        run_agent(question)

if st.session_state.notice:
    kind, message = st.session_state.notice
    (st.warning if kind == "warning" else st.error)(message)

if st.session_state.report:
    render_report(st.session_state.report)
