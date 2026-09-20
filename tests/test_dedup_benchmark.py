import pytest
from literax.engine.benchmark import DeduplicationBenchmarkSuite, DedupBenchmarkResult

def test_dedup_benchmark_generation():
    papers, expected_unique, cluster_map = DeduplicationBenchmarkSuite.generate_benchmark_dataset(base_count=10)
    assert len(papers) > 10
    assert expected_unique == 10
    assert len(cluster_map) == len(papers)
