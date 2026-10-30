"""Source quality: classify, score, filter, and cap confidence in code."""
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


def compute_confidence(llm_level: str, independent_domains: int, fetches_ok: int,
                       tool_errors: int, used_fallback: bool) -> str:
    """Final confidence = min(LLM's claim, evidence-based cap)."""
    cap = _LEVEL["high"]
    if used_fallback or independent_domains < 2:
        cap = _LEVEL["low"]
    elif independent_domains < 3 or fetches_ok == 0 or tool_errors > 0:
        cap = _LEVEL["medium"]
    return _NAME[min(_LEVEL.get(llm_level, 0), cap)]
