# 🌐 OpenAlex Integration Guide

**OpenAlex** is an open and comprehensive catalog of the global research system, containing over 250 million scientific works, authors, institutions, and venues.

---

## 🚀 Key Advantages

1. **Fully Open Access**: Requires no paid subscription or developer approval.
2. **Rich Graph Model**: Links papers to concepts, funding agencies, and open access PDF locations.
3. **High Rate Limits**: Free access allows up to 100,000 requests per day in the polite pool.

---

## 📧 The Polite Pool

By providing a valid email address in the `mailto` parameter or `User-Agent` header, requests are routed through OpenAlex's fast "polite pool" with dedicated capacity:

```env
OPENALEX_EMAIL=your.email@university.edu
```

```http
GET /works?search=machine+learning+phishing+detection&mailto=your.email@university.edu HTTP/1.1
Host: api.openalex.org
```

---

## 🧩 Abstract Inverted Index Decoding

OpenAlex stores abstracts as an **inverted index** (mapping words to arrays of character positions) to conserve bandwidth. LiteraX automatically reconstructs standard plain text abstracts:

```python
from typing import Dict, List, Optional

def reconstruct_openalex_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """Decodes OpenAlex abstract_inverted_index into continuous text."""
    if not inverted_index:
        return None
        
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
            
    # Sort by character/word position
    word_positions.sort(key=lambda x: x[0])
    return " ".join([word for _, word in word_positions])
```

---

## 💻 OpenAlex Provider Implementation

```python
import httpx
from typing import List
from literax.providers.base import ResearchProvider, Paper, SearchQuery, Author

class OpenAlexProvider(ResearchProvider):
    name = "OpenAlex"

    def __init__(self, email: str):
        self.email = email
        self.base_url = "https://api.openalex.org/works"

    async def search(self, query: SearchQuery) -> List[Paper]:
        params = {
            "search": query.raw_query,
            "per_page": query.limit,
            "mailto": self.email
        }
        if query.open_access_only:
            params["filter"] = "is_oa:true"

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(self.base_url, params=params)
            if resp.status_code != 200:
                return []

            results = resp.json().get("results", [])
            papers = []
            for item in results:
                abstract = reconstruct_openalex_abstract(item.get("abstract_inverted_index"))
                oa_location = item.get("best_oa_location") or {}
                
                authors = [
                    Author(name=auth.get("author", {}).get("display_name", ""))
                    for auth in item.get("authorships", [])
                ]

                papers.append(Paper(
                    id=item.get("id"),
                    title=item.get("display_name", ""),
                    abstract=abstract,
                    doi=item.get("doi"),
                    year=item.get("publication_year"),
                    authors=authors,
                    journal=item.get("primary_location", {}).get("source", {}).get("display_name"),
                    citation_count=item.get("cited_by_count", 0),
                    source="OpenAlex",
                    open_access=item.get("is_oa", False),
                    full_text_url=oa_location.get("pdf_url")
                ))
            return papers
```
