import pytest
from literax.models import Paper, Author
from literax.synthesis.citation import CitationGenerator

def test_citation_generation():
    paper = Paper(
        id="cose_2025",
        title="Machine Learning Approaches for Phishing URL Detection",
        authors=[Author(name="Ahmad Rahman"), Author(name="Sanjay Kumar")],
        journal="Computers & Security",
        year=2025,
        doi="10.1016/j.cose.2024.103982",
        source="Elsevier"
    )

    apa = CitationGenerator.to_apa(paper)
    assert "Rahman" in apa
    assert "(2025)" in apa
    assert "https://doi.org/10.1016/j.cose.2024.103982" in apa

    bibtex = CitationGenerator.to_bibtex(paper)
    assert "@article{" in bibtex
    assert "rahman2025machine" in bibtex
    assert "Computers & Security" in bibtex
