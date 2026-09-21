import pytest
from literax.models import Paper, Author, SearchQuery

def test_paper_properties():
    author1 = Author(name="Alan Turing")
    author2 = Author(name="Ada Lovelace")
    
    paper_with_doi = Paper(
        id="p1",
        title="Computing Machinery and Intelligence",
        doi="10.1093/mind/LIX.236.433",
        authors=[author1, author2],
        source="Mind"
    )
    
    assert paper_with_doi.has_doi is True
    assert paper_with_doi.primary_author == "Alan Turing"

    paper_without_doi = Paper(
        id="p2",
        title="Theoretical Paper",
        doi=None,
        authors=[],
        source="Preprint"
    )
    
    assert paper_without_doi.has_doi is False
    assert paper_without_doi.primary_author == "Anonymous"

def test_search_query_defaults():
    query = SearchQuery(raw_query="machine learning")
    assert query.limit == 10
    assert query.open_access_only is False
    assert query.expanded_queries == []
