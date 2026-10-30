from app.ranking import (assess_evidence, classify_source, compute_confidence,
                         entity_coverage, rank_and_filter)


def item(url, score):
    return {"title": "t", "url": url, "content": "c", "score": score}


def test_classify_source():
    assert classify_source("https://arxiv.org/abs/1") == "research"
    assert classify_source("https://docs.qdrant.tech/x") == "official"
    assert classify_source("https://github.com/a/b") == "official"
    assert classify_source("https://techcrunch.com/x") == "news"
    assert classify_source("https://random-blog.io/x") == "other"


def test_filters_low_scores_and_caps_domain():
    items = [item("https://a.com/1", 0.9), item("https://a.com/2", 0.8),
             item("https://a.com/3", 0.7), item("https://b.com/1", 0.1),
             item("https://pinterest.com/p", 0.6)]
    out = rank_and_filter(items)
    urls = [i["url"] for i in out]
    assert urls.count("https://a.com/3") == 0       # domain cap = 2
    assert "https://b.com/1" not in urls            # below threshold
    assert "https://pinterest.com/p" not in urls    # low-quality domain penalised


def test_never_returns_empty_if_input_exists():
    assert len(rank_and_filter([item("https://a.com", 0.01)])) == 1


def test_assess_evidence():
    assert assess_evidence([])[0] is True
    three = [item(f"https://s{i}.com", 0.9) for i in range(3)]
    assert assess_evidence(three)[0] is False


def test_confidence_caps():
    assert compute_confidence("high", 4, 2, 0, False) == "high"
    assert compute_confidence("high", 2, 2, 0, False) == "medium"
    assert compute_confidence("high", 4, 0, 0, False) == "medium"
    assert compute_confidence("high", 4, 2, 1, False) == "medium"
    assert compute_confidence("high", 1, 2, 0, False) == "low"
    assert compute_confidence("high", 4, 2, 0, True) == "low"
    assert compute_confidence("low", 4, 2, 0, False) == "low"


def test_entity_coverage_detects_unrelated_sources():
    q = "Research the quarterly revenue of Zzyzx Quantum Llamas Incorporated"
    cov, missing = entity_coverage(q, ["Quantum Computing Inc. reports revenue"])
    assert cov < 0.6 and "Zzyzx" in missing and "Llamas" in missing


def test_entity_coverage_ok_when_names_present_or_absent():
    assert entity_coverage("Compare Pinecone and Qdrant", ["pinecone vs qdrant"])[0] == 1.0
    assert entity_coverage("What is RAG?", ["anything"]) == (1.0, [])
    assert entity_coverage("Research the pros and cons of agents", ["x"]) == (1.0, [])


def test_low_entity_coverage_caps_confidence():
    assert compute_confidence("high", 4, 2, 0, False, entity_cov=0.25) == "low"
    assert compute_confidence("high", 4, 2, 0, False, entity_cov=1.0) == "high"