import math
from typing import List
from rapidfuzz import fuzz
from literax.models import Paper

class RelevanceRanker:
    """Multi-Factor Relevance Ranking Engine."""

    CURRENT_YEAR = 2026

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
        paper_year = paper.year or 2020
        year_diff = max(0, cls.CURRENT_YEAR - paper_year)
        s_recency = math.exp(-0.08 * year_diff)

        # 4. Citation impact (Logarithmic scaling)
        s_citation = min(1.0, math.log10(paper.citation_count + 1) / 3.0)

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
