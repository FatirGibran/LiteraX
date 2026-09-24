import pytest
from literax.models import Paper, Author, SearchQuery, ResearchGapItem, TokenCorrection

def test_paper_properties():
    author1 = Author(name="Alan Turing")
    author2 = Author(name="Ada Lovelace")
    
    paper_with_doi = Paper(
        id="p1",
        title="  Computing Machinery and Intelligence  ",
        doi="10.1093/mind/LIX.236.433",
        year=2024,
        authors=[author1, author2],
        source="Mind"
    )
    
    assert paper_with_doi.has_doi is True
    assert paper_with_doi.primary_author == "Alan Turing"
    assert paper_with_doi.is_recent is True
    assert paper_with_doi.display_title == "Computing Machinery and Intelligence"
    assert paper_with_doi.is_highly_cited is False

    paper_with_doi.citation_count = 150
    assert paper_with_doi.is_highly_cited is True
    assert paper_with_doi.doi_url == "https://doi.org/10.1093/mind/LIX.236.433"
    assert paper_with_doi.direct_url == "https://doi.org/10.1093/mind/LIX.236.433"
    assert "artikel rujukan utama" in paper_with_doi.relevance_reasoning

    assert paper_with_doi.authors_summary == "Turing & Lovelace"
    assert paper_with_doi.year_str == "2024"
    assert paper_with_doi.has_full_text is False
    assert paper_with_doi.has_abstract is False

    paper_with_doi.full_text_url = "https://example.com/paper.pdf"
    paper_with_doi.abstract = "An insightful exploration of computing machinery."
    assert paper_with_doi.has_full_text is True
    assert paper_with_doi.has_abstract is True

    paper_without_doi = Paper(
        id="p2",
        title="Theoretical Paper",
        doi=None,
        authors=[],
        source="Preprint"
    )
    
    assert paper_without_doi.has_doi is False
    assert paper_without_doi.primary_author == "Anonymous"
    assert paper_without_doi.authors_summary == "Anonymous"
    assert paper_without_doi.year_str == "n.d."
    assert paper_without_doi.has_full_text is False
    assert paper_without_doi.has_abstract is False

def test_paper_authors_summary_variants():
    # Single author
    p1 = Paper(id="1", title="T1", source="S", authors=[Author(name="Grace Hopper")])
    assert p1.authors_summary == "Hopper"

    # Three authors
    p3 = Paper(
        id="3",
        title="T3",
        source="S",
        authors=[Author(name="Grace Hopper"), Author(name="Claude Shannon"), Author(name="John von Neumann")]
    )
    assert p3.authors_summary == "Hopper et al."

def test_paper_to_summary_dict():
    paper = Paper(
        id="p100",
        title="Attention Is All You Need",
        doi="10.5555/3295222.3295349",
        year=2017,
        authors=[Author(name="Ashish Vaswani"), Author(name="Noam Shazeer")],
        journal="NeurIPS",
        citation_count=100000,
        source="ArXiv",
        open_access=True,
        full_text_url="https://arxiv.org/pdf/1706.03762.pdf"
    )
    summary = paper.to_summary_dict()
    assert summary["id"] == "p100"
    assert summary["title"] == "Attention Is All You Need"
    assert summary["authors"] == "Vaswani & Shazeer"
    assert summary["year"] == 2017
    assert summary["journal"] == "NeurIPS"
    assert summary["citations"] == 100000
    assert summary["source"] == "ArXiv"
    assert summary["doi"] == "10.5555/3295222.3295349"
    assert summary["direct_url"] == "https://arxiv.org/pdf/1706.03762.pdf"
    assert summary["open_access"] is True

def test_search_query_defaults():
    query = SearchQuery(raw_query="machine learning")
    assert query.limit == 10
    assert query.open_access_only is False
    assert query.expanded_queries == []

def test_author_properties():
    author1 = Author(name="  Nikola Tesla  ", affiliation="Wardenclyffe Lab")
    assert author1.display_name == "Nikola Tesla"
    assert author1.has_affiliation is True

    author2 = Author(name="Thomas Edison", affiliation=None)
    assert author2.display_name == "Thomas Edison"
    assert author2.has_affiliation is False

def test_research_gap_item_properties():
    gap1 = ResearchGapItem(
        title="Scalability in High-Throughput IoT",
        description="Current models exhibit inference latency exceeding 100ms.",
        category="Scalability",
        severity="High",
        supporting_papers=["paper_1", "paper_2"]
    )
    assert gap1.is_high_severity is True
    assert gap1.supporting_count == 2

    gap2 = ResearchGapItem(
        title="Dataset Bias in Low-Resource Languages",
        description="Lack of balanced corpus for regional dialects.",
        category="Dataset",
        severity="Medium",
        supporting_papers=[]
    )
    assert gap2.is_high_severity is False
    assert gap2.supporting_count == 0

def test_token_correction_properties():
    t1 = TokenCorrection(original="machne", corrected="machine", status="CORRECTED", confidence=0.92)
    assert t1.is_corrected is True
    assert t1.is_protected is False

    t2 = TokenCorrection(original="svm", corrected="svm", status="PROTECTED", confidence=1.0)
    assert t2.is_corrected is False
    assert t2.is_protected is True

    t3 = TokenCorrection(original="learning", corrected="learning", status="UNCHANGED", confidence=1.0)
    assert t3.is_corrected is False
    assert t3.is_protected is False
