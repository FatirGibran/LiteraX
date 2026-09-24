import pytest
from literax.models import Paper, Author, BrainstormResult
from literax.synthesis.brainstormer import ResearchBrainstormer

def test_brainstormer_generation_basic():
    result = ResearchBrainstormer.generate("deteksi phishing url")
    assert isinstance(result, BrainstormResult)
    assert result.topic == "deteksi phishing url"
    assert result.total_ideas == 3
    assert len(result.ideas) == 3

    # Verify Idea 1 contents
    idea1 = result.ideas[0]
    assert idea1.title_id != ""
    assert idea1.title_en != ""
    assert len(idea1.suggested_methods) >= 2
    assert idea1.novelty_points != ""
    assert idea1.expected_contribution != ""

    # Verify datasets and challenges
    assert len(result.benchmark_datasets) >= 2
    assert len(result.practical_challenges) >= 2

def test_brainstormer_with_seed_papers():
    p1 = Paper(
        id="p_transformer",
        title="Transformer-Based Adversarial Robustness in IoT",
        abstract="We evaluate Transformer models against adversarial evasion attacks on network traffic.",
        authors=[Author(name="Alice")],
        year=2024,
        doi="10.1000/182",
        source="Scopus",
        full_text_url="https://example.com/paper.pdf"
    )
    result = ResearchBrainstormer.generate("IoT Security", seed_papers=[p1])
    assert len(result.seed_papers) == 1
    assert result.seed_papers[0].title == p1.title

    md = ResearchBrainstormer.to_markdown(result)
    assert "RESEARCH BRAINSTORMING DOSSIER" in md
    assert "IoT Security" in md
    assert "https://example.com/paper.pdf" in md
    assert "REKOMENDASI 3 TOPIK / JUDUL RISET" in md

def test_brainstorm_result_get_idea():
    result = ResearchBrainstormer.generate("NLP")
    assert result.get_idea(0) is not None
    assert result.get_idea(0).title_id != ""
    assert result.get_idea(1) is not None
    assert result.get_idea(2) is not None
    assert result.get_idea(3) is None
    assert result.get_idea(-1) is None
