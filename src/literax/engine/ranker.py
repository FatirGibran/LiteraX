import math
from typing import List, Optional
from rapidfuzz import fuzz
from literax.models import Paper

class RelevanceRanker:
    """Multi-Factor Relevance Ranking Engine."""

    CURRENT_YEAR = 2026

    @classmethod
    def calculate_recency_score(cls, year: Optional[int], current_year: int = CURRENT_YEAR) -> float:
        """Calculates exponential decay recency score based on publication year."""
        paper_year = year or 2020
        year_diff = max(0, current_year - paper_year)
        return math.exp(-0.08 * year_diff)

    @classmethod
    def calculate_citation_score(cls, citation_count: int) -> float:
        """Calculates normalized logarithmic citation score scaled between 0.0 and 1.0."""
        return min(1.0, math.log10(max(0, citation_count) + 1) / 3.0)

    @classmethod
    def calculate_score(cls, query: str, paper: Paper) -> float:
        query_lower = query.lower()
        title_lower = paper.title.lower()
        abstract_lower = (paper.abstract or "").lower()

        # 1. Semantic / Token similarity (RapidFuzz partial/token set ratio)
        s_semantic = fuzz.token_set_ratio(query_lower, f"{title_lower} {abstract_lower}") / 100.0

        # 2. Lexical match (Title exact overlap)
        s_bm25 = fuzz.partial_ratio(query_lower, title_lower) / 100.0

        # 3. Recency score (Exponential decay)
        s_recency = cls.calculate_recency_score(paper.year)

        # 4. Citation impact (Logarithmic scaling)
        s_citation = cls.calculate_citation_score(paper.citation_count)

        # 5. Source quality tier
        source_lower = paper.source.lower()
        if "scopus" in source_lower or "sinta 1" in source_lower:
            s_source = 1.0
        elif "openalex" in source_lower or "crossref" in source_lower:
            s_source = 0.9
        else:
            s_source = 0.8

        composite = (
            0.35 * s_semantic +
            0.25 * s_bm25 +
            0.15 * s_recency +
            0.15 * s_citation +
            0.10 * s_source
        )

        return min(1.0, round(composite, 3))

    @classmethod
    def rank(cls, query: str, papers: List[Paper]) -> List[Paper]:
        """Calculates relevance scores and sorts papers in descending order."""
        for p in papers:
            p.composite_relevance = cls.calculate_score(query, p)

        return sorted(papers, key=lambda x: x.composite_relevance, reverse=True)
