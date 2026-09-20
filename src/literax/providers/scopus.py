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
