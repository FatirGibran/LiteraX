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

    @property
    def is_authenticated(self) -> bool:
        """Returns True if Scopus API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    def _build_query_string(self, query: SearchQuery) -> str:
        """Translates search query into Scopus TITLE-ABS-KEY syntax."""
        query_str = f"TITLE-ABS-KEY({query.raw_query})"
        if query.year_start and query.year_end:
            query_str += f" AND PUBYEAR >= {query.year_start} AND PUBYEAR <= {query.year_end}"
        elif query.year_start:
            query_str += f" AND PUBYEAR >= {query.year_start}"
        return query_str

    async def search(self, query: SearchQuery) -> List[Paper]:
        """Searches Scopus database using TITLE-ABS-KEY query syntax."""
        if not self.api_key:
            return []

        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json"
        }
        if self.inst_token:
            headers["X-ELS-Insttoken"] = self.inst_token

        params = {
            "query": self._build_query_string(query),
            "count": query.limit
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self.base_url, headers=headers, params=params)
                if resp.status_code != 200:
                    return []

                data = resp.json()
                entries = data.get("search-results", {}).get("entry", [])
                papers: List[Paper] = []

                for entry in entries:
                    if "error" in entry:
                        continue

                    title = entry.get("dc:title", "Untitled")
                    doi = entry.get("prism:doi")
                    scopus_id = entry.get("dc:identifier", "").replace("SCOPUS_ID:", "")

                    authors: List[Author] = []
                    creator = entry.get("dc:creator")
                    if creator:
                        authors.append(Author(name=creator))

                    cover_date = entry.get("prism:coverDate", "")
                    year = int(cover_date[:4]) if len(cover_date) >= 4 and cover_date[:4].isdigit() else None

                    citedby = entry.get("citedby-count", 0)
                    try:
                        citation_count = int(citedby)
                    except (ValueError, TypeError):
                        citation_count = 0

                    oa_flag = entry.get("openaccessFlag", False)
                    open_access = bool(oa_flag and str(oa_flag).lower() in ["true", "1"])

                    links = entry.get("link", [])
                    landing_page = None
                    for link in links:
                        if link.get("@ref") == "scopus":
                            landing_page = link.get("@href")
                            break
                    if not landing_page and doi:
                        landing_page = f"https://doi.org/{doi}"

                    papers.append(Paper(
                        id=f"scopus_{scopus_id}" if scopus_id else (doi or f"scopus_{abs(hash(title))}"),
                        title=title,
                        abstract=entry.get("dc:description"),
                        doi=doi,
                        year=year,
                        authors=authors,
                        journal=entry.get("prism:publicationName"),
                        citation_count=citation_count,
                        source=self.name,
                        open_access=open_access,
                        landing_page_url=landing_page
                    ))

                return papers
        except Exception:
            return []

    async def get_paper(self, identifier: str) -> Optional[Paper]:
        """Fetches metadata for a single paper by Scopus ID or DOI."""
        if not self.api_key:
            return None

        clean_id = identifier.replace("https://doi.org/", "").replace("SCOPUS_ID:", "")
        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json"
        }
        if self.inst_token:
            headers["X-ELS-Insttoken"] = self.inst_token

        url = f"https://api.elsevier.com/content/abstract/scopus_id/{clean_id}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json().get("abstracts-retrieval-response", {})
                    coredata = data.get("coredata", {})
                    title = coredata.get("dc:title", "Untitled")
                    doi = coredata.get("prism:doi")
                    cover_date = coredata.get("prism:coverDate", "")
                    year = int(cover_date[:4]) if len(cover_date) >= 4 and cover_date[:4].isdigit() else None

                    return Paper(
                        id=f"scopus_{clean_id}",
                        title=title,
                        abstract=coredata.get("dc:description"),
                        doi=doi,
                        year=year,
                        journal=coredata.get("prism:publicationName"),
                        source=self.name
                    )
        except Exception:
            pass
        return None

    async def get_citation(self, identifier: str, style: str = "apa") -> str:
        """Retrieves formatted citation string via DOI resolution."""
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
