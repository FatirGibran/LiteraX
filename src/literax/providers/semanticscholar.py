import httpx
from typing import List, Optional
from literax.providers.base import ResearchProvider
from literax.models import Paper, SearchQuery, Author

class SemanticScholarProvider(ResearchProvider):
    """Semantic Scholar Academic Graph Provider."""

    name = "Semantic Scholar"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def search(self, query: SearchQuery) -> List[Paper]:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        params = {
            "query": query.raw_query,
            "limit": query.limit,
            "fields": "paperId,title,abstract,year,authors,citationCount,isOpenAccess,openAccessPdf,externalIds,venue"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.base_url, headers=headers, params=params)
                if resp.status_code != 200:
                    return []

                data = resp.json().get("data", [])
                papers: List[Paper] = []
                for item in data:
                    external_ids = item.get("externalIds") or {}
                    oa_pdf = item.get("openAccessPdf") or {}

                    authors = [
                        Author(name=auth.get("name", "Unknown"))
                        for auth in item.get("authors", [])
                    ]

                    doi = external_ids.get("DOI")

                    papers.append(Paper(
                        id=item.get("paperId", ""),
                        title=item.get("title") or "Untitled",
                        abstract=item.get("abstract"),
                        doi=doi,
                        year=item.get("year"),
                        authors=authors,
                        journal=item.get("venue"),
                        citation_count=item.get("citationCount", 0),
                        source=self.name,
                        open_access=item.get("isOpenAccess", False),
                        full_text_url=oa_pdf.get("url"),
                        landing_page_url=f"https://www.semanticscholar.org/paper/{item.get('paperId')}"
                    ))
                return papers
        except Exception:
            return []

    async def get_paper(self, identifier: str) -> Optional[Paper]:
        return None

    async def get_citation(self, identifier: str, style: str = "apa") -> str:
        return ""
