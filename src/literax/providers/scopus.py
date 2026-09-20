import httpx
from typing import List, Optional
from literax.providers.base import ResearchProvider
from literax.models import Paper, SearchQuery, Author
from literax.config import settings

class ScopusProvider(ResearchProvider):
    """Elsevier Scopus REST API Provider with institutional token support."""

    name = "Scopus"
    requires_auth = True

    def __init__(
        self,
        api_key: Optional[str] = None,
        inst_token: Optional[str] = None,
        base_url: str = "https://api.elsevier.com/content/search/scopus"
    ):
        self.api_key = api_key or settings.scopus_api_key
        self.inst_token = inst_token or settings.scopus_insttoken
        self.base_url = base_url

    def _build_query_string(self, query: SearchQuery) -> str:
        """Translates search query into Scopus TITLE-ABS-KEY syntax."""
        query_str = f"TITLE-ABS-KEY({query.raw_query})"
        if query.year_start and query.year_end:
            query_str += f" AND PUBYEAR >= {query.year_start} AND PUBYEAR <= {query.year_end}"
        elif query.year_start:
            query_str += f" AND PUBYEAR >= {query.year_start}"
        return query_str
