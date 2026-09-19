# 🧠 Semantic Scholar Integration Guide

**Semantic Scholar** (by the Allen Institute for AI) provides an AI-powered academic graph containing over 200 million research papers with citation contexts, influence scores, and neural embeddings.

---

## 🚀 Key Advantages

1. **Influential Citations**: Identifies which citations are central to a paper rather than mere passing references.
2. **Pre-computed SPECTER Embeddings**: Provides 768-dimensional paper embeddings for semantic similarity comparisons.
3. **Open Access PDF Resolution**: Direct access to legal PDF URLs hosted across institutional repositories.

---

## 🔑 Authentication & Limits

- **Public Tier (No API Key)**:
  - Rate limit: 1 request per second.
  - Endpoint: `https://api.semanticscholar.org/graph/v1/`
- **Partner Tier (API Key)**:
  - Rate limit: 10 requests per second.
  - Header: `x-api-key: your_api_key_here`

```env
SEMANTIC_SCHOLAR_API_KEY=your_key_here
```

---

## 💻 Semantic Scholar Provider Implementation

```python
import httpx
from typing import List
from literax.providers.base import ResearchProvider, Paper, SearchQuery, Author

class SemanticScholarProvider(ResearchProvider):
    name = "Semantic Scholar"

    def __init__(self, api_key: str | None = None):
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

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(self.base_url, headers=headers, params=params)
            if resp.status_code != 200:
                return []

            data = resp.json().get("data", [])
            papers = []
            for item in data:
                external_ids = item.get("externalIds") or {}
                oa_pdf = item.get("openAccessPdf") or {}

                authors = [
                    Author(name=auth.get("name", ""))
                    for auth in item.get("authors", [])
                ]

                papers.append(Paper(
                    id=item.get("paperId", ""),
                    title=item.get("title", ""),
                    abstract=item.get("abstract"),
                    doi=external_ids.get("DOI"),
                    year=item.get("year"),
                    authors=authors,
                    journal=item.get("venue"),
                    citation_count=item.get("citationCount", 0),
                    source="Semantic Scholar",
                    open_access=item.get("isOpenAccess", False),
                    full_text_url=oa_pdf.get("url")
                ))
            return papers
```
