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
