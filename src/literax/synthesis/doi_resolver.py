import re
import time
import httpx
from typing import Dict, Tuple, Optional, Any

class DoiResolver:
    """Automated DOI Resolution engine via Crossref Content Negotiation with TTL caching."""

    def __init__(self, ttl_seconds: int = 3600, max_cache_size: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_cache_size = max_cache_size
        self._cache: Dict[Tuple[str, str], Tuple[str, float]] = {}
        self.hits: int = 0
        self.misses: int = 0

    @staticmethod
    def normalize_doi(doi: str) -> str:
        """Strips URL prefixes, resolver hosts, and extra whitespace from DOIs."""
        if not doi:
            return ""
        clean = doi.strip()
        clean = re.sub(r"^https?://(dx\.)?doi\.org/", "", clean, flags=re.I)
        clean = re.sub(r"^doi:\s*", "", clean, flags=re.I)
        return clean.strip()
