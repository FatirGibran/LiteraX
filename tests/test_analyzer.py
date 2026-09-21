import pytest
from literax.models import Paper
from literax.synthesis.analyzer import PaperAnalyzer

def test_heuristic_extract_with_known_algos():
    paper = Paper(
        id="p_ml",
        title="Deep Learning and Random Forest for Phishing Classification",
        abstract="In this research, we evaluate Random Forest and CNN models on dataset NSL-KDD. Our approach achieves 98% Accuracy and high F1-Score.",
        source="IEEE"
    )
    analysis = PaperAnalyzer.heuristic_extract(paper)

    assert "Random Forest" in analysis.algorithms_used or "CNN" in analysis.algorithms_used
    assert "Accuracy" in analysis.evaluation_metrics
    assert analysis.title == paper.title
    assert "NSL-KDD" in analysis.dataset

def test_to_markdown_summary():
    paper = Paper(
        id="p_md",
        title="Graph Neural Networks in Cybersecurity",
        abstract="We propose a novel framework for malware detection.",
        source="ArXiv"
    )
    analysis = PaperAnalyzer.heuristic_extract(paper)
    md = PaperAnalyzer.to_markdown_summary(analysis)
    assert "### 📑 Graph Neural Networks in Cybersecurity" in md
    assert "**🎯 Objective:**" in md
    assert "**🔬 Methodology:**" in md
