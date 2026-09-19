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
