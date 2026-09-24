import re
from typing import List, Dict, Optional
from rapidfuzz import fuzz
from literax.models import Paper

class Deduplicator:
    """4-Tier Deduplication Engine for merging multi-source academic papers."""

    DEFAULT_TITLE_SIMILARITY_THRESHOLD: float = 0.88

    @staticmethod
    def normalize_doi(doi: Optional[str]) -> Optional[str]:
        """Normalizes a DOI string by removing HTTP prefixes, resolver domains, and lowercasing."""
        if not doi:
            return None
        clean = doi.strip().lower()
        clean = re.sub(r"^https?://(dx\.)?doi\.org/", "", clean)
        return clean.strip()

    @staticmethod
    def normalize_title(title: str) -> str:
        """Strips punctuation and collapses whitespace for fuzzy title comparison."""
        clean = title.lower()
        clean = re.sub(r"[^\w\s]", "", clean)
        return re.sub(r"\s+", " ", clean).strip()

    @classmethod
    def are_duplicates(cls, p1: Paper, p2: Paper, title_threshold: float = DEFAULT_TITLE_SIMILARITY_THRESHOLD) -> bool:
        """Determines if two paper instances refer to the same scholarly publication."""
        # Tier 1: Canonical Normalized DOI match
        doi1 = cls.normalize_doi(p1.doi)
        doi2 = cls.normalize_doi(p2.doi)
        if doi1 and doi2:
            return doi1 == doi2

        # Tier 2: Title similarity + Publication Year
        norm_t1 = cls.normalize_title(p1.title)
        norm_t2 = cls.normalize_title(p2.title)

        title_sim = fuzz.ratio(norm_t1, norm_t2) / 100.0
        if title_sim < title_threshold:
            return False

        # If publication year exists on both, verify within 1 year delta
        if p1.year and p2.year:
            if abs(p1.year - p2.year) > 1:
                return False

        # Tier 3: First author surname match if authors present
        if p1.authors and p2.authors:
            a1 = p1.authors[0].name.lower().split()[-1] if p1.authors[0].name else ""
            a2 = p2.authors[0].name.lower().split()[-1] if p2.authors[0].name else ""
            if a1 and a2 and a1 != a2:
                # Different author surnames
                return False

        return True

    @classmethod
    def merge_papers(cls, p1: Paper, p2: Paper) -> Paper:
        """Merges two duplicate paper records preserving the richest attributes."""
        primary, secondary = (p1, p2) if len(p1.abstract or "") >= len(p2.abstract or "") else (p2, p1)

        merged_doi = primary.doi or secondary.doi
        merged_abstract = primary.abstract or secondary.abstract
        merged_year = primary.year or secondary.year
        merged_journal = primary.journal or secondary.journal
        merged_citation = max(primary.citation_count, secondary.citation_count)
        merged_oa = primary.open_access or secondary.open_access
        merged_full_text = primary.full_text_url or secondary.full_text_url

        # Source aggregation
        sources = sorted(list(set([s.strip() for s in f"{primary.source}, {secondary.source}".split(",")])))

        return Paper(
            id=primary.id,
            title=primary.title,
            abstract=merged_abstract,
            doi=merged_doi,
            year=merged_year,
            authors=primary.authors or secondary.authors,
            journal=merged_journal,
            citation_count=merged_citation,
            source=", ".join(sources),
            open_access=merged_oa,
            full_text_url=merged_full_text,
            landing_page_url=primary.landing_page_url or secondary.landing_page_url
        )

    @classmethod
    def deduplicate(cls, papers: List[Paper], title_threshold: float = DEFAULT_TITLE_SIMILARITY_THRESHOLD) -> List[Paper]:
        """Deduplicates a list of papers and returns unique combined papers."""
        unique_papers: List[Paper] = []

        for candidate in papers:
            matched_idx = -1
            for i, existing in enumerate(unique_papers):
                if cls.are_duplicates(existing, candidate, title_threshold=title_threshold):
                    matched_idx = i
                    break

            if matched_idx != -1:
                unique_papers[matched_idx] = cls.merge_papers(unique_papers[matched_idx], candidate)
            else:
                unique_papers.append(candidate)

        return unique_papers

    @classmethod
    def get_duplicate_clusters(cls, papers: List[Paper], title_threshold: float = DEFAULT_TITLE_SIMILARITY_THRESHOLD) -> List[List[Paper]]:
        """Groups candidate papers into duplicate clusters for inspection and auditing."""
        clusters: List[List[Paper]] = []

        for candidate in papers:
            matched_idx = -1
            for i, cluster in enumerate(clusters):
                if cls.are_duplicates(cluster[0], candidate, title_threshold=title_threshold):
                    matched_idx = i
                    break

            if matched_idx != -1:
                clusters[matched_idx].append(candidate)
            else:
                clusters.append([candidate])

        return clusters
