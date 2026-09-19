# 🔬 Elsevier Scopus Integration Guide

**Scopus** is Elsevier's curated abstract and citation database of peer-reviewed literature: scientific journals, books, and conference proceedings.

---

## 🔑 Authentication Credentials

Elsevier requires two levels of authentication:
1. **API Key (`SCOPUS_API_KEY`)**: Issued via the [Elsevier Developer Portal](https://dev.elsevier.com/).
2. **Institutional Token (`SCOPUS_INSTTOKEN`)**: Required if accessing Scopus off-campus or without an authorized institutional static IP.

### Environment Configuration (`.env`)

```env
SCOPUS_API_KEY=your_elsevier_api_key_here
SCOPUS_INSTTOKEN=your_institutional_token_here
SCOPUS_BASE_URL=https://api.elsevier.com/content/search/scopus
```

---

## 📡 API Request Structure

### Required Headers
```http
GET /content/search/scopus?query=TITLE-ABS-KEY(phishing+detection+AND+"machine+learning")&count=10 HTTP/1.1
Host: api.elsevier.com
X-ELS-APIKey: your_elsevier_api_key_here
X-ELS-Insttoken: your_institutional_token_here
Accept: application/json
```

### Scopus Search Query Syntax
LiteraX maps user queries into Scopus field codes:
- `TITLE-ABS-KEY(...)`: Searches within title, abstract, and author keywords.
- `PUBYEAR > 2021`: Restricts results to recent years.
- `DOCTYPE(ar OR cp)`: Filters for research articles or conference papers.

---

## 💻 Scopus Provider Implementation

```python
import httpx
from typing import List
from literax.providers.base import ResearchProvider, Paper, SearchQuery, Author

class ScopusProvider(ResearchProvider):
    name = "Scopus"
    requires_auth = True

    def __init__(self, api_key: str, inst_token: str | None = None):
        self.api_key = api_key
        self.inst_token = inst_token
        self.base_url = "https://api.elsevier.com/content/search/scopus"

    async def search(self, query: SearchQuery) -> List[Paper]:
        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json"
        }
        if self.inst_token:
            headers["X-ELS-Insttoken"] = self.inst_token

        params = {
            "query": f"TITLE-ABS-KEY({query.raw_query})",
            "count": query.limit
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.base_url, headers=headers, params=params)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            entries = data.get("search-results", {}).get("entry", [])
            papers = []
            for entry in entries:
                papers.append(Paper(
                    id=entry.get("dc:identifier", ""),
                    title=entry.get("dc:title", "Untitled"),
                    doi=entry.get("prism:doi"),
                    year=int(entry.get("prism:coverDate", "2024")[:4]),
                    journal=entry.get("prism:publicationName"),
                    citation_count=int(entry.get("citedby-count", 0)),
                    source="Scopus",
                    open_access=entry.get("openaccessFlag", False)
                ))
            return papers
```

---

## ⚖️ Quotas & Limits

- **Rate Limits**: Elsevier imposes weekly quota limits per API Key (typically 10,000 to 20,000 requests/week depending on institutional tier).
- **Headers to Monitor**:
  - `X-RateLimit-Limit`: Total allowed requests in the window.
  - `X-RateLimit-Remaining`: Remaining allowance.
  - `X-RateLimit-Reset`: Unix timestamp when the quota resets.
- When `X-RateLimit-Remaining` falls below 50, LiteraX automatically switches to fallback providers (OpenAlex and Semantic Scholar).
