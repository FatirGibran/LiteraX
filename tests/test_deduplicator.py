import pytest
from literax.models import Paper, Author
from literax.engine.deduplicator import Deduplicator

def test_deduplicator_doi_match():
    p1 = Paper(
        id="openalex_1",
        title="Machine Learning Approaches for Phishing",
        doi="10.1016/j.cose.2024.103982",
        source="OpenAlex",
        citation_count=10
    )
    p2 = Paper(
        id="crossref_1",
        title="Machine Learning Approaches for Phishing: An Empirical Study",
        doi="https://doi.org/10.1016/j.cose.2024.103982",
        source="Crossref",
        citation_count=25
    )

    assert Deduplicator.are_duplicates(p1, p2)
    merged = Deduplicator.merge_papers(p1, p2)
    assert merged.doi == "10.1016/j.cose.2024.103982"
    assert merged.citation_count == 25
    assert "Crossref" in merged.source and "OpenAlex" in merged.source

def test_deduplicator_fuzzy_title_match():
    p1 = Paper(
        id="p1",
        title="Phishing Detection with Neural Networks in Banking",
        year=2024,
        authors=[Author(name="A. Rahman")],
        source="SourceA"
    )
    p2 = Paper(
        id="p2",
        title="Phishing Detection with Neural Networks in Banking Systems",
        year=2024,
        authors=[Author(name="Ali Rahman")],
        source="SourceB"
    )

    papers = Deduplicator.deduplicate([p1, p2])
    assert len(papers) == 1

def test_deduplicator_custom_threshold():
    p1 = Paper(
        id="t1",
        title="Deep Reinforcement Learning for Autonomous Driving",
        year=2023,
        source="Conference"
    )
    p2 = Paper(
        id="t2",
        title="Deep Reinforcement Learning for Cooperative Autonomous Driving",
        year=2023,
        source="Journal"
    )
    # With a very high threshold (0.99), these are distinct
    assert not Deduplicator.are_duplicates(p1, p2, title_threshold=0.99)

def test_deduplicator_get_duplicate_clusters():
    p1 = Paper(id="p1", title="Quantum Computing Algorithms", doi="10.1000/1", source="S1")
    p2 = Paper(id="p2", title="Quantum Computing Algorithms", doi="10.1000/1", source="S2")
    p3 = Paper(id="p3", title="Unrelated Machine Learning Study", doi="10.1000/2", source="S3")

    clusters = Deduplicator.get_duplicate_clusters([p1, p2, p3])
    assert len(clusters) == 2
    assert len(clusters[0]) == 2
    assert len(clusters[1]) == 1
    assert {p.id for p in clusters[0]} == {"p1", "p2"}
    assert clusters[1][0].id == "p3"
    # With a lower threshold (0.75), these might match
    assert Deduplicator.are_duplicates(p1, p2, title_threshold=0.75)
