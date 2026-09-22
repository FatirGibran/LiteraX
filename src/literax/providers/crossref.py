import httpx
from typing import List, Optional
from literax.providers.base import ResearchProvider
from literax.models import Paper, SearchQuery, Author

class CrossrefProvider(ResearchProvider):
    """Crossref REST API Provider (DOI Authority, >150M records)."""

    name = "Crossref"
    requires_auth = False

    def __init__(self, mailto: str = "researcher@university.ac.id", base_url: str = "https://api.crossref.org/works"):
        self.mailto = mailto
        self.base_url = base_url

    @staticmethod
    def clean_query_string(raw_query: str) -> str:
        """Sanitizes query string by stripping excess whitespace and control characters."""
        return " ".join(raw_query.strip().split())

    async def search(self, query: SearchQuery) -> List[Paper]:
        headers = {
            "User-Agent": f"LiteraX-Bot/1.0 (mailto:{self.mailto})"
        }
        params = {
            "query": self.clean_query_string(query.raw_query),
            "rows": query.limit,
            "select": "DOI,title,author,published-print,published-online,is-referenced-by-count,container-title,abstract"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.base_url, headers=headers, params=params)
                if resp.status_code != 200:
                    return []

                items = resp.json().get("message", {}).get("items", [])
                papers: List[Paper] = []
                for item in items:
                    titles = item.get("title", [])
                    title = titles[0] if titles else "Untitled"

                    authors = [
                        Author(name=f"{a.get('given', '')} {a.get('family', '')}".strip() or "Unknown")
                        for a in item.get("author", [])
                    ]

                    # Parse year
                    year = None
                    date_parts = (
                        item.get("published-print", {}).get("date-parts")
                        or item.get("published-online", {}).get("date-parts")
                        or [[]]
                    )[0]
                    if date_parts:
                        year = date_parts[0]

                    doi = item.get("DOI")

                    papers.append(Paper(
                        id=doi or f"crossref_{hash(title)}",
                        title=title,
                        abstract=item.get("abstract"),
                        doi=doi,
                        year=year,
                        authors=authors,
                        journal=(item.get("container-title") or [""])[0],
                        citation_count=item.get("is-referenced-by-count", 0),
                        source=self.name,
                        open_access=False,
                        landing_page_url=f"https://doi.org/{doi}" if doi else None
                    ))
                return papers
        except Exception:
            return []

    async def get_paper(self, identifier: str) -> Optional[Paper]:
        clean_doi = identifier.replace("https://doi.org/", "")
        url = f"{self.base_url}/{clean_doi}"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, headers={"User-Agent": f"LiteraX-Bot/1.0 (mailto:{self.mailto})"})
                if resp.status_code == 200:
                    item = resp.json().get("message", {})
                    return Paper(
                        id=clean_doi,
                        title=(item.get("title") or ["Untitled"])[0],
                        abstract=item.get("abstract"),
                        doi=clean_doi,
                        source=self.name
                    )
        except Exception:
            pass
        return None

    async def get_citation(self, identifier: str, style: str = "apa") -> str:
        clean_doi = identifier.replace("https://doi.org/", "")
        url = f"https://doi.org/{clean_doi}"
        headers = {"Accept": f"text/x-bibliography; style={style}"}
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=8.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.text.strip()
        except Exception:
            pass
        return ""
