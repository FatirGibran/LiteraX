# 🏷️ Crossref Integration Guide

**Crossref** is the official Digital Object Identifier (DOI) registration agency for scholarly publications, containing metadata for more than 150 million journal articles, books, standards, and datasets.

---

## 🎯 Role in LiteraX

Crossref acts as LiteraX's **primary metadata authority**:
1. **DOI Resolution**: Resolving any DOI directly to validated bibliographic metadata.
2. **Citation Formats**: Serving authoritative BibTeX and APA strings via HTTP content negotiation.
3. **Publisher Linking**: Locating publisher landing pages and open access licenses.

---

## 📧 Crossref Polite Pool

Crossref operates a dedicated polite pool for clients that identify themselves:

```env
CROSSREF_MAILTO=researcher@university.ac.id
```

Requests should include this in the `User-Agent`:
```http
User-Agent: LiteraX-Academic-Bot/1.0 (mailto:researcher@university.ac.id)
```

---

## 📡 Key Endpoints

### 1. Search Works
```http
GET https://api.crossref.org/works?query=phishing+detection+machine+learning&rows=10
```

### 2. Direct DOI Lookup
```http
GET https://api.crossref.org/works/10.1016/j.cose.2024.103982
```

### 3. Native Citation Content Negotiation
Instead of parsing JSON, LiteraX can query Crossref directly with formatting headers:

```python
import httpx

async def fetch_bibtex_from_doi(doi: str) -> str:
    clean_doi = doi.replace("https://doi.org/", "")
    url = f"https://doi.org/{clean_doi}"
    headers = {"Accept": "application/x-bibtex"}
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.text
        return ""
```

---

## 💻 Crossref Provider Implementation

```python
import httpx
from typing import List
from literax.providers.base import ResearchProvider, Paper, SearchQuery, Author

class CrossrefProvider(ResearchProvider):
    name = "Crossref"

    def __init__(self, mailto: str):
        self.mailto = mailto
        self.base_url = "https://api.crossref.org/works"

    async def search(self, query: SearchQuery) -> List[Paper]:
        headers = {
            "User-Agent": f"LiteraX-Bot/1.0 (mailto:{self.mailto})"
        }
        params = {
            "query": query.raw_query,
            "rows": query.limit,
            "select": "DOI,title,author,published-print,is-referenced-by-count,container-title,abstract"
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(self.base_url, headers=headers, params=params)
            if resp.status_code != 200:
                return []

            items = resp.json().get("message", {}).get("items", [])
            papers = []
            for item in items:
                titles = item.get("title", [])
                title = titles[0] if titles else "Untitled"
                
                authors = [
                    Author(name=f"{a.get('given', '')} {a.get('family', '')}".strip())
                    for a in item.get("author", [])
                ]

                # Parse publication year from parts
                year = None
                date_parts = item.get("published-print", {}).get("date-parts", [[]])[0]
                if date_parts:
                    year = date_parts[0]

                papers.append(Paper(
                    id=item.get("DOI", ""),
                    title=title,
                    abstract=item.get("abstract"),
                    doi=item.get("DOI"),
                    year=year,
                    authors=authors,
                    journal=(item.get("container-title") or [""])[0],
                    citation_count=item.get("is-referenced-by-count", 0),
                    source="Crossref",
                    open_access=False
                ))
            return papers
```
