import re
import time
import httpx
from typing import Dict, Tuple, Optional, Any

class DoiResolver:
    """Automated DOI Resolution engine via Crossref Content Negotiation with TTL caching."""

    STYLE_ACCEPT_MAP: Dict[str, str] = {
        "apa": "text/x-bibliography; style=apa",
        "ieee": "text/x-bibliography; style=ieee",
        "harvard": "text/x-bibliography; style=harvard3",
        "chicago": "text/x-bibliography; style=chicago-author-date",
        "vancouver": "text/x-bibliography; style=vancouver",
        "bibtex": "application/x-bibtex",
        "ris": "application/x-research-info-systems",
        "json": "application/citeproc+json",
        "csl": "application/citeproc+json"
    }

    def __init__(self, ttl_seconds: int = 3600, max_cache_size: int = 1000):
        self.ttl_seconds = ttl_seconds
        self.max_cache_size = max_cache_size
        self._cache: Dict[Tuple[str, str], Tuple[str, float]] = {}
        self.hits: int = 0
        self.misses: int = 0

    @property
    def supported_styles(self) -> list[str]:
        """Returns list of supported style keys in content negotiation map."""
        return list(self.STYLE_ACCEPT_MAP.keys())

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

    def is_cached(self, doi: str, style: str) -> bool:
        """Checks if a valid, unexpired cached citation exists for the DOI."""
        key = (self.normalize_doi(doi).lower(), style.lower())
        if key in self._cache:
            _, exp = self._cache[key]
            return time.time() < exp
        return False

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    @property
    def cache_hit_rate(self) -> float:
        """Returns the hit rate ratio (0.0 to 1.0) of the cache."""
        total = self.hits + self.misses
        return round(self.hits / total, 3) if total > 0 else 0.0

    async def resolve(
        self,
        doi: str,
        style: str = "apa",
        timeout: float = 8.0,
        client: Optional[httpx.AsyncClient] = None
    ) -> Optional[str]:
        """Resolves formatted citation or metadata for a given DOI using content negotiation."""
        clean_doi = self.normalize_doi(doi)
        if not clean_doi:
            return None

        style_clean = style.lower().strip()
        cached = self.get_cached(clean_doi, style_clean)
        if cached:
            return cached

        accept_header = self.STYLE_ACCEPT_MAP.get(style_clean, f"text/x-bibliography; style={style_clean}")
        headers = {
            "Accept": accept_header,
            "User-Agent": "LiteraX-DOI-Resolver/1.0 (mailto:researcher@university.ac.id)"
        }
        url = f"https://doi.org/{clean_doi}"

        try:
            if client is not None:
                resp = await client.get(url, headers=headers, follow_redirects=True, timeout=timeout)
                if resp.status_code == 200:
                    text = resp.text.strip()
                    self.set_cache(clean_doi, style_clean, text)
                    return text
            else:
                async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as internal_client:
                    resp = await internal_client.get(url, headers=headers)
                    if resp.status_code == 200:
                        text = resp.text.strip()
                        self.set_cache(clean_doi, style_clean, text)
                        return text
        except Exception:
            pass

        return None

default_doi_resolver = DoiResolver()
