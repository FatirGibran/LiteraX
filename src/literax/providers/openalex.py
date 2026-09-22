import httpx
from typing import List, Optional, Dict
from literax.providers.base import ResearchProvider
from literax.models import Paper, SearchQuery, Author

class OpenAlexProvider(ResearchProvider):
    """OpenAlex API Provider (Open Access, >250M works)."""

    name = "OpenAlex"
    requires_auth = False

    def __init__(self, email: str = "researcher@university.ac.id", base_url: str = "https://api.openalex.org/works"):
        self.email = email
        self.base_url = base_url

    @staticmethod
    def decode_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
        """Decodes OpenAlex abstract_inverted_index into text."""
        if not inverted_index or not isinstance(inverted_index, dict):
            return None
        pairs = []
        for word, positions in inverted_index.items():
            if not isinstance(positions, list):
                continue
            for pos in positions:
                if isinstance(pos, int):
                    pairs.append((pos, word))
        if not pairs:
            return None
        pairs.sort(key=lambda x: x[0])
        return " ".join([w for _, w in pairs])

    async def search(self, query: SearchQuery) -> List[Paper]:
        params = {
            "search": query.raw_query,
            "per_page": query.limit,
            "mailto": self.email
        }
        if query.open_access_only:
            params["filter"] = "is_oa:true"

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code != 200:
                    return []

                results = resp.json().get("results", [])
                papers: List[Paper] = []
                for item in results:
                    abstract = self.decode_abstract(item.get("abstract_inverted_index"))
                    oa_loc = item.get("best_oa_location") or {}
                    
                    authors = [
                        Author(name=auth.get("author", {}).get("display_name", "Unknown"))
                        for auth in item.get("authorships", [])
                    ]

                    doi_raw = item.get("doi")
                    doi_clean = doi_raw.replace("https://doi.org/", "") if doi_raw else None

                    papers.append(Paper(
                        id=item.get("id", ""),
                        title=item.get("display_name") or "Untitled",
                        abstract=abstract,
                        doi=doi_clean,
                        year=item.get("publication_year"),
                        authors=authors,
                        journal=(item.get("primary_location") or {}).get("source", {}).get("display_name"),
                        citation_count=item.get("cited_by_count", 0),
                        source=self.name,
                        open_access=item.get("is_oa", False),
                        full_text_url=oa_loc.get("pdf_url"),
                        landing_page_url=item.get("doi") or item.get("id")
                    ))
                return papers
        except Exception as e:
            # Safe network fallback
            return []

    async def get_paper(self, identifier: str) -> Optional[Paper]:
        # Implementation for single paper fetch
        return None

    async def get_citation(self, identifier: str, style: str = "apa") -> str:
        return ""
