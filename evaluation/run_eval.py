"""Run all eval queries through the agent and write evaluation/results.json + a markdown table.

Usage:  python -m evaluation.run_eval [--only Q1,Q3]
"""
import argparse
import json
import os
import time

from app.agent import run_research

HERE = os.path.dirname(__file__)


def check(case: dict, report) -> dict:
    text = report.model_dump_json().lower()
    hits = sum(1 for k in case.get("must_mention", []) if k in text)
    domains = {str(s.url).split("/")[2] for s in report.sources}
    leaked = [s for s in case.get("forbid_substrings", []) if s.lower() in text]
    conf_ok = (report.confidence_level == "low") if case.get("expect_low_confidence") else True
    return {
        "keyword_hits": hits,
        "keywords_ok": hits >= case.get("min_keywords", 0),
        "independent_domains": len(domains),
        "every_finding_cited": all(f.source_urls for f in report.key_findings),
        "leaked": leaked,
        "confidence_ok": conf_ok,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="Comma-separated query ids")
    args = parser.parse_args()
    cases = json.load(open(os.path.join(HERE, "queries.json"), encoding="utf-8"))
    if args.only:
        wanted = set(args.only.split(","))
        cases = [c for c in cases if c["id"] in wanted]

    results = []
    for case in cases:
        print(f"\n=== {case['id']} ({case['type']}): {case['query']}")
        t0 = time.perf_counter()
        row = {"id": case["id"], "type": case["type"], "query": case["query"]}
        try:
            report = run_research(case["query"])
            meta = report.metadata
            row.update(status="ok", confidence=report.confidence_level,
                       latency_s=round(time.perf_counter() - t0, 1),
                       fallback=meta.used_fallback, tool_errors=meta.tool_errors,
                       reformulated=meta.reformulated, tokens=meta.prompt_tokens + meta.output_tokens,
                       **check(case, report))
        except Exception as exc:  # a graceful refusal is a valid outcome for edge cases
            row.update(status=f"failed: {type(exc).__name__}: {exc}",
                       latency_s=round(time.perf_counter() - t0, 1))
        results.append(row)

    out = os.path.join(HERE, "results.json")
    json.dump(results, open(out, "w", encoding="utf-8"), indent=2)

    print("\n| id | type | status | conf | domains | keywords | fallback | latency | tokens |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        print(f"| {r['id']} | {r['type']} | {r['status'][:18]} | {r.get('confidence','-')} | "
              f"{r.get('independent_domains','-')} | {r.get('keywords_ok','-')} | "
              f"{r.get('fallback','-')} | {r['latency_s']}s | {r.get('tokens','-')} |")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
