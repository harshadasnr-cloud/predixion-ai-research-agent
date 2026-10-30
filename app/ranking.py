"""Source quality: classify, score, filter, and cap confidence in code."""
import re
from urllib.parse import urlparse

from app import config

RESEARCH_DOMAINS = {"arxiv.org", "acm.org", "ieee.org", "nature.com",
                    "semanticscholar.org", "openreview.net", "aclanthology.org"}
OFFICIAL_DOMAINS = {"github.com", "readthedocs.io", "python.org"}
NEWS_DOMAINS = {"techcrunch.com", "reuters.com", "bloomberg.com", "theverge.com",
                "wsj.com", "nytimes.com", "inc42.com", "yourstory.com",
                "economictimes.indiatimes.com"}
LOW_QUALITY_DOMAINS = {"pinterest.com", "quora.com", "facebook.com",
                       "instagram.com", "tiktok.com"}

_LEVEL = {"low": 0, "medium": 1, "high": 2}
_NAME = {v: k for k, v in _LEVEL.items()}


def domain_of(url) -> str:
    host = (urlparse(str(url)).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def _matches(host: str, domains: set[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


def classify_source(url) -> str:
    host = domain_of(url)
    if _matches(host, RESEARCH_DOMAINS):
        return "research"
    if (host.endswith((".gov", ".edu"))
            or host.startswith(("docs.", "developer.", "developers."))
            or _matches(host, OFFICIAL_DOMAINS)):
        return "official"
    if _matches(host, NEWS_DOMAINS):
        return "news"
    return "other"


def effective_score(item: dict) -> float:
    raw = item.get("score")
    base = float(raw) if isinstance(raw, (int, float)) else 0.5
    if _matches(domain_of(item["url"]), LOW_QUALITY_DOMAINS):
        return base * 0.3
    if classify_source(item["url"]) in {"official", "research"}:
        return base * 1.15
    return base


def rank_and_filter(items: list[dict], min_score=None, max_per_domain=None) -> list[dict]:
    min_score = config.MIN_SCORE if min_score is None else min_score
    max_per_domain = max_per_domain or config.MAX_PER_DOMAIN

    scored = sorted(
        (dict(i, rank_score=round(effective_score(i), 3)) for i in items),
        key=lambda i: i["rank_score"],
        reverse=True,
    )
    kept = [i for i in scored if i["rank_score"] >= min_score] or scored[:2]

    per_domain: dict[str, int] = {}
    result = []
    for item in kept:
        d = domain_of(item["url"])
        if per_domain.get(d, 0) >= max_per_domain:
            continue
        per_domain[d] = per_domain.get(d, 0) + 1
        result.append(item)
    return result


def assess_evidence(items: list[dict]) -> tuple[bool, str]:
    """Is the evidence too thin to answer? Drives the adaptive re-search."""
    if len(items) < 3:
        return True, "fewer than 3 usable sources"
    if len({domain_of(i["url"]) for i in items}) < 2:
        return True, "sources come from a single domain"
    return False, ""


_SKIP_TERMS = {"Compare", "Find", "Research", "What", "Which", "Explain", "Describe",
               "Summarize", "Analyze", "Tell", "Give", "List", "Show", "Identify",
               "Evaluate", "The", "And", "For", "With", "From", "Into", "About", "Based"}
MIN_ENTITY_COVERAGE = 0.6


def entity_coverage(question: str, texts: list[str]) -> tuple[float, list[str]]:
    """Do the question's key names (Title-case words) appear in the evidence?

    Returns (coverage 0..1, missing terms). No names in the question -> (1.0, []).
    Catches questions about things the sources are not actually about.
    """
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", question)
    terms: list[str] = []
    for w in words[1:]:  # skip the first word, it is capitalised anyway
        if (len(w) >= 4 and w[0].isupper() and any(c.islower() for c in w)
                and w not in _SKIP_TERMS and w.lower() not in {t.lower() for t in terms}):
            terms.append(w)
    if not terms:
        return 1.0, []
    blob = " ".join(texts).lower()
    missing = [t for t in terms if t.lower() not in blob]
    return (len(terms) - len(missing)) / len(terms), missing


def compute_confidence(llm_level: str, independent_domains: int, fetches_ok: int,
                       tool_errors: int, used_fallback: bool,
                       entity_cov: float = 1.0) -> str:
    """Final confidence = min(LLM's claim, evidence-based cap)."""
    cap = _LEVEL["high"]
    if used_fallback or independent_domains < 2 or entity_cov < MIN_ENTITY_COVERAGE:
        cap = _LEVEL["low"]
    elif independent_domains < 3 or fetches_ok == 0 or tool_errors > 0:
        cap = _LEVEL["medium"]
    return _NAME[min(_LEVEL.get(llm_level, 0), cap)]