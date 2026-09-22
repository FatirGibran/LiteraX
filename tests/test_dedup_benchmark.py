import pytest
from literax.engine.benchmark import DeduplicationBenchmarkSuite, DedupBenchmarkResult

def test_dedup_benchmark_generation():
    papers, expected_unique, cluster_map = DeduplicationBenchmarkSuite.generate_benchmark_dataset(base_count=10)
    assert len(papers) > 10
    assert expected_unique == 10
    assert len(cluster_map) == len(papers)

def test_dedup_benchmark_execution():
    result = DeduplicationBenchmarkSuite.run_benchmark(base_count=15)
    assert isinstance(result, DedupBenchmarkResult)
    assert result.total_input > 15
    assert result.expected_unique == 15
    assert result.precision > 0.8
    assert result.recall > 0.8
    assert result.f1_score > 0.8
    assert result.throughput_papers_per_sec > 0
    assert result.elapsed_seconds >= 0

def test_dedup_benchmark_to_markdown_table():
    res = DedupBenchmarkResult(
        total_input=100,
        expected_unique=50,
        actual_unique=50,
        true_positives=50,
        false_positives=0,
        false_negatives=0,
        precision=1.0,
        recall=1.0,
        f1_score=1.0,
        elapsed_seconds=0.05,
        throughput_papers_per_sec=2000.0
    )
    md = res.to_markdown_table()
    assert "| Total Input Papers | 100 |" in md
    assert "| F1-Score | 100.0% |" in md
    assert "| Throughput | 2000.0 papers/sec |" in md
