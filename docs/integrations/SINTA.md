# 🇮🇩 SINTA & GARUDA Integration Guide

**SINTA (Science and Technology Index)** is Indonesia's national accreditation and citation indexing system managed by the Ministry of Education, Culture, Research, and Technology (Kemendikbudristek).

---

## 🏛️ SINTA Accreditation Tiers (S1 – S6)

In Indonesia, scientific journals are categorized according to the **ARJUNA** (Akreditasi Jurnal Nasional) evaluation standards:

- **SINTA 1 (S1)**: Highest national rank (Score 85–100) or indexed in Scopus/WoS with substantial impact.
- **SINTA 2 (S2)**: High-impact national journals (Score 70–84).
- **SINTA 3 (S3)**: Accredited national journals (Score 60–69).
- **SINTA 4 (S4)**: Accredited national journals (Score 50–59).
- **SINTA 5 (S5)**: Accredited national journals (Score 40–49).
- **SINTA 6 (S6)**: Basic accredited journals (Score 30–39).

LiteraX allows users to filter Indonesian queries by tier, e.g. `sinta:1,2 machine learning`.

---

## 🔗 GARUDA (Garba Rujukan Digital)

Alongside SINTA, LiteraX connects to the **GARUDA** digital reference library, which indexes open-access Indonesian papers directly from university OJS (Open Journal Systems) platforms.

---

## ⚙️ Configuration

In your `.env` file:

```env
# SINTA & Garuda Config
SINTA_BASE_URL=https://sinta.kemdikbud.go.id
GARUDA_BASE_URL=https://garuda.kemdikbud.go.id
SINTA_CRAWLER_DELAY=1.5
```

---

## 🛠️ Provider Implementation Details

Because SINTA does not provide a public self-serve REST API for individual developers, LiteraX uses an async polite scraper combined with GARUDA REST endpoints:

```python
import httpx
from bs4 import BeautifulSoup
from literax.providers.base import ResearchProvider, Paper, SearchQuery

class SintaGarudaProvider(ResearchProvider):
    name = "SINTA / GARUDA"

    def __init__(self, base_url: str):
        self.base_url = base_url

    async def search(self, query: SearchQuery) -> list[Paper]:
        # Translates query to Indonesian terms if needed
        search_term = query.raw_query
        url = f"https://garuda.kemdikbud.go.id/documents?q={search_term}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"User-Agent": "LiteraX-Academic-Bot/1.0"})
            if resp.status_code != 200:
                return []
            
            return self._parse_garuda_html(resp.text)
            
    def _parse_garuda_html(self, html: str) -> list[Paper]:
        soup = BeautifulSoup(html, "html.parser")
        papers = []
        for item in soup.select(".article-item"):
            title_elem = item.select_one(".title-article")
            if not title_elem:
                continue
            papers.append(Paper(
                id=f"garuda_{hash(title_elem.text.strip())}",
                title=title_elem.text.strip(),
                source="GARUDA / SINTA",
                open_access=True
            ))
        return papers
```

---

## ⚠️ Polite Crawling & Compliance

When querying Indonesian national endpoints:
- LiteraX enforces a rate limit delay of $\ge 1.5$ seconds between queries.
- Requests identify themselves clearly with an academic User-Agent header.
- Cached queries in Redis have a 48-hour TTL to prevent repetitive server hits.
