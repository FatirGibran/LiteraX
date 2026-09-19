import httpx
from bs4 import BeautifulSoup
from typing import List, Optional
from literax.providers.base import ResearchProvider
from literax.models import Paper, SearchQuery, Author

class SintaGarudaProvider(ResearchProvider):
    """Indonesian SINTA & GARUDA Scientific Portal Adapter."""

    name = "GARUDA / SINTA"

    def __init__(self, base_url: str = "https://garuda.kemdikbud.go.id"):
        self.base_url = base_url

    async def search(self, query: SearchQuery) -> List[Paper]:
        url = f"{self.base_url}/documents?q={query.raw_query}"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers={"User-Agent": "LiteraX-Academic-Bot/1.0"})
                if resp.status_code != 200:
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                papers: List[Paper] = []
                for item in soup.select(".article-item"):
                    title_elem = item.select_one(".title-article")
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()

                    author_elem = item.select_one(".author-article")
                    authors = []
                    if author_elem:
                        for a in author_elem.text.split(","):
                            if a.strip():
                                authors.append(Author(name=a.strip()))

                    abstract_elem = item.select_one(".abstract-article")
                    abstract = abstract_elem.text.strip() if abstract_elem else None

                    papers.append(Paper(
                        id=f"garuda_{abs(hash(title))}",
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        source=self.name,
                        open_access=True,
                        landing_page_url=url
                    ))
                return papers
        except Exception:
            return []

    async def get_paper(self, identifier: str) -> Optional[Paper]:
        return None

    async def get_citation(self, identifier: str, style: str = "apa") -> str:
        return ""
