import time
import random
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel

from literax.models import Paper, Author
from literax.engine.deduplicator import Deduplicator

class DedupBenchmarkResult(BaseModel):
    total_input: int
    expected_unique: int
    actual_unique: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    elapsed_seconds: float
    throughput_papers_per_sec: float

    def to_markdown_table(self) -> str:
        """Formats the benchmark result into a summary Markdown table."""
        return (
            "| Metric | Value |\n"
            "| :--- | :---: |\n"
            f"| Total Input Papers | {self.total_input} |\n"
            f"| Expected Unique | {self.expected_unique} |\n"
            f"| Actual Unique | {self.actual_unique} |\n"
            f"| Precision | {self.precision * 100:.1f}% |\n"
            f"| Recall | {self.recall * 100:.1f}% |\n"
            f"| F1-Score | {self.f1_score * 100:.1f}% |\n"
            f"| Throughput | {self.throughput_papers_per_sec:.1f} papers/sec |"
        )

class DeduplicationBenchmarkSuite:
    """Automated benchmark suite for evaluating deduplication accuracy, precision, recall, and throughput."""

    @classmethod
    def generate_benchmark_dataset(cls, base_count: int = 50) -> Tuple[List[Paper], int, Dict[str, str]]:
        """Generates synthetic dataset with ground-truth duplicate clusters and noise."""
        papers: List[Paper] = []
        cluster_map: Dict[str, str] = {}

        sample_titles = [
            "Deep Learning Approaches for Phishing Website Detection",
            "An Empirical Study on Multi-Factor Fuzzy Logic for Query Normalization",
            "Transformer-Based Scientific Text Summarization with Domain Adapters",
            "Blockchain-Enabled Secure Federated Learning in Internet of Things",
            "Zero-Day Malware Detection using Graph Neural Networks and Dynamic Analysis",
            "Automated Research Gap Identification using Citation Graph Mining",
            "Evaluation of Retrieval Augmented Generation for Academic Question Answering",
            "Lightweight Convolutional Networks for Embedded Edge Device Inference",
            "Cross-Lingual Information Retrieval in Bilingual Academic Repositories",
            "Robust Adversarial Defense for Network Intrusion Detection Systems"
        ]

        expected_unique = 0

        for i in range(base_count):
            cluster_id = f"cluster_{i}"
            expected_unique += 1
            base_title = sample_titles[i % len(sample_titles)] + f" - Study {i}"
            base_doi = f"10.1016/j.literax.{2020 + (i % 6)}.{100000 + i}"

            p_orig = Paper(
                id=f"orig_{i}",
                title=base_title,
                abstract=f"Abstract of study {i} discussing core methodologies and experimental results.",
                doi=base_doi,
                year=2024,
                authors=[Author(name=f"Author {i} Family"), Author(name="Jane Coauthor")],
                journal="Journal of Academic Computing",
                citation_count=10 + i,
                source="OpenAlex"
            )
            papers.append(p_orig)
            cluster_map[p_orig.id] = cluster_id

            p_dup1 = Paper(
                id=f"dup_crossref_{i}",
                title=base_title.lower(),
                abstract=f"Full extended abstract of study {i} discussing core methodologies and experimental results.",
                doi=f"https://doi.org/{base_doi.upper()}",
                year=2024,
                authors=[Author(name=f"A. {i} Family")],
                journal="J. Acad. Comput.",
                citation_count=12 + i,
                source="Crossref"
            )
            papers.append(p_dup1)
            cluster_map[p_dup1.id] = cluster_id

            if i % 2 == 0:
                p_dup2 = Paper(
                    id=f"dup_scopus_{i}",
                    title=base_title.replace(" - Study", ": Study"),
                    abstract=None,
                    doi=None,
                    year=2024,
                    authors=[Author(name=f"Author {i} Family")],
                    journal="Journal of Academic Computing",
                    citation_count=11 + i,
                    source="Scopus"
                )
                papers.append(p_dup2)
                cluster_map[p_dup2.id] = cluster_id

        random.seed(42)
        random.shuffle(papers)
        return papers, expected_unique, cluster_map

    @classmethod
    def run_benchmark(cls, base_count: int = 50) -> DedupBenchmarkResult:
        """Executes full deduplication benchmark and computes information retrieval metrics."""
        papers, expected_unique, cluster_map = cls.generate_benchmark_dataset(base_count)
        total_input = len(papers)

        start_time = time.perf_counter()
        deduplicated = Deduplicator.deduplicate(papers)
        elapsed = time.perf_counter() - start_time

        actual_unique = len(deduplicated)
        true_positives = (total_input - actual_unique)
        expected_merges = (total_input - expected_unique)

        if actual_unique <= expected_unique:
            false_positives = expected_unique - actual_unique
            false_negatives = 0
        else:
            false_positives = 0
            false_negatives = actual_unique - expected_unique

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 1.0
        recall = true_positives / expected_merges if expected_merges > 0 else 1.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        throughput = total_input / elapsed if elapsed > 0 else 0.0

        return DedupBenchmarkResult(
            total_input=total_input,
            expected_unique=expected_unique,
            actual_unique=actual_unique,
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            elapsed_seconds=round(elapsed, 4),
            throughput_papers_per_sec=round(throughput, 1)
        )
