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

    def get_cached(self, doi: str, style: str) -> Optional[str]:
        """Retrieves cached resolution if not expired."""
        key = (self.normalize_doi(doi).lower(), style.lower())
        if key in self._cache:
            val, exp = self._cache[key]
            if time.time() < exp:
                self.hits += 1
                return val
            else:
                del self._cache[key]
        self.misses += 1
        return None

    def set_cache(self, doi: str, style: str, content: str) -> None:
        """Stores resolved content in cache with eviction when full."""
        if len(self._cache) >= self.max_cache_size:
            keys_to_remove = list(self._cache.keys())[: max(1, self.max_cache_size // 5)]
            for k in keys_to_remove:
                self._cache.pop(k, None)

        key = (self.normalize_doi(doi).lower(), style.lower())
        self._cache[key] = (content, time.time() + self.ttl_seconds)

    def clear_cache(self) -> None:
        """Clears all cached entries and resets metrics."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    @property
    def cache_size(self) -> int:
        return len(self._cache)
