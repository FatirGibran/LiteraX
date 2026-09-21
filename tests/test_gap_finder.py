import pytest
from literax.models import Paper
from literax.synthesis.gap_finder import ResearchGapFinder

def test_find_gaps_empty():
    report = ResearchGapFinder.find_gaps("Blockchain in Healthcare", [])
    assert report.topic == "Blockchain in Healthcare"
    assert len(report.gaps) == 0

def test_find_gaps_with_papers():
    p1 = Paper(
        id="g1",
        title="Random Forest for Network Intrusion",
        abstract="We use Random Forest and Decision Tree classifiers.",
        source="Springer"
    )
    p2 = Paper(
        id="g2",
        title="Transformer and CNN for Network Defense",
        abstract="Deep learning transformer models achieve superior detection.",
        source="IEEE"
    )

    report = ResearchGapFinder.find_gaps("Intrusion Detection", [p1, p2])
    assert report.topic == "Intrusion Detection"
    assert len(report.gaps) == 3
    categories = [g.category for g in report.gaps]
    assert "Methodology" in categories
    assert "Dataset" in categories
    assert "Scalability" in categories
