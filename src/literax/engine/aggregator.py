import asyncio
from typing import List, Optional
from literax.providers.base import ResearchProvider
from literax.providers.openalex import OpenAlexProvider
from literax.providers.crossref import CrossrefProvider
from literax.providers.semanticscholar import SemanticScholarProvider
from literax.providers.sinta_garuda import SintaGarudaProvider
from literax.engine.deduplicator import Deduplicator
from literax.engine.ranker import RelevanceRanker
from literax.models import Paper, SearchQuery

class PaperAggregator:
    """Coordinates concurrent searches across academic providers, deduplicates, and ranks."""

    def __init__(self, providers: Optional[List[ResearchProvider]] = None):
        self.providers = providers or [
            OpenAlexProvider(),
            CrossrefProvider(),
            SemanticScholarProvider(),
            SintaGarudaProvider()
        ]

    async def search(self, query: SearchQuery) -> List[Paper]:
        """Searches all matching providers concurrently with error containment."""
        active_providers = self.providers
        if query.providers:
            provider_names = [p.lower() for p in query.providers]
            active_providers = [
                p for p in self.providers
                if any(name in p.name.lower() for name in provider_names)
            ] or self.providers

        tasks = [provider.search(query) for provider in active_providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_papers: List[Paper] = []
        for provider, res in zip(active_providers, results):
            if isinstance(res, list):
                raw_papers.extend(res)

        # Deduplicate
        unique_papers = Deduplicator.deduplicate(raw_papers)

        # Rank
        ranked_papers = RelevanceRanker.rank(query.raw_query, unique_papers)

        return ranked_papers[:query.limit]
