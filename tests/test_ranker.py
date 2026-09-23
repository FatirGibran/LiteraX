import pytest
from literax.models import Paper
from literax.engine.ranker import RelevanceRanker

def test_ranker_ordering():
    p_irrelevant = Paper(
        id="1",
        title="Agricultural Irrigation Techniques in Dry Lands",
        abstract="This paper discusses drip irrigation for farming crops.",
        source="Generic",
        year=2015,
        citation_count=1
    )
    p_relevant = Paper(
        id="2",
        title="Machine Learning for Phishing URL Detection: A Survey",
        abstract="Phishing websites evade traditional blacklists. This survey compares machine learning classifiers.",
        source="Scopus",
        year=2025,
        citation_count=80
    )

    ranked = RelevanceRanker.rank("machine learning phishing detection", [p_irrelevant, p_relevant])
    assert ranked[0].id == "2"
    assert ranked[0].composite_relevance > ranked[1].composite_relevance

def test_recency_scoring():
    # Newer papers should have higher recency score than older ones
    recent = RelevanceRanker.calculate_recency_score(2025, current_year=2026)
    old = RelevanceRanker.calculate_recency_score(2010, current_year=2026)
    assert recent > old
    assert recent <= 1.0
    assert old >= 0.0

def test_citation_scoring():
    zero_cite = RelevanceRanker.calculate_citation_score(0)
    high_cite = RelevanceRanker.calculate_citation_score(1000)
    assert zero_cite == 0.0
    assert high_cite <= 1.0
    assert high_cite > zero_cite

def test_ranker_priority():
    p_scopus = Paper(
        id="scopus_1",
        title="Deep Learning for Network Intrusion Detection",
        abstract="Deep neural networks for intrusion detection in enterprise networks.",
        source="Scopus",
        year=2023,
        citation_count=10
    )
    p_sinta = Paper(
        id="sinta_1",
        title="Deep Learning untuk Klasifikasi Trafik Jaringan",
        abstract="Implementasi deep learning untuk deteksi intrusi jaringan lokal.",
        source="GARUDA / SINTA",
        year=2024,
        citation_count=15
    )

    # 1. Scopus first
    prio_scopus = RelevanceRanker.rank("deep learning intrusion detection", [p_sinta, p_scopus], priority="scopus")
    assert prio_scopus[0].id == "scopus_1"
    assert prio_scopus[1].id == "sinta_1"

    # 2. SINTA first
    prio_sinta = RelevanceRanker.rank("deep learning intrusion detection", [p_scopus, p_sinta], priority="sinta")
    assert prio_sinta[0].id == "sinta_1"
    assert prio_sinta[1].id == "scopus_1"

