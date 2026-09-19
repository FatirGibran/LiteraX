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
