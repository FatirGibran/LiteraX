# 🌐 Academic Data Sources & Provider Directory

LiteraX queries both global academic databases and regional indexes. This document catalogs all supported providers, their authentication requirements, licensing models, and access tiers.

---

## 📊 Provider Comparison Matrix

| Provider | Coverage | Access Model | Auth Required? | Rate Limit / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAlex** | >250M works | Open Access | No (Polite Pool requires email) | 10 req/sec (polite) |
| **Crossref** | >150M records | Open Access | No (Polite Pool requires email) | 50 req/sec |
| **Semantic Scholar** | >200M works | Open / Freemium | Optional API Key | 1 req/sec without key; 10 req/sec with key |
| **Elsevier Scopus** | >90M records | Commercial / Subscription | Yes (API Key + InstToken) | Weekly quota based on license |
| **SINTA (Indonesia)** | Accredited ID Journals (S1-S6) | Open / Crawler / API | Institutional / Token | Governed by Kemdikbudristek |
| **GARUDA** | Indonesian publications | Open Access | No | Indonesian scientific portal |
| **DOAJ** | >20,000 OA Journals | Open Access | No | Direct REST API |
| **arXiv** | >2.4M preprints | Open Access | No | Max 1 req/3 sec |
| **PubMed** | >36M biomedical | Open Access | Optional NCBI API Key | 3 req/sec (10 req/sec with key) |

---

## 🔑 Authentication Categories

LiteraX categorizes providers into two operational pools:

### 1. Zero-Credential Open Access Pool
These sources require no paid subscription and work out-of-the-box:
- **OpenAlex**
- **Crossref**
- **Semantic Scholar** (Public tier)
- **DOAJ**
- **arXiv**
- **PubMed**

To activate high-speed polite pools for OpenAlex and Crossref, provide your email address in `.env`:
```env
OPENALEX_EMAIL=researcher@university.ac.id
CROSSREF_MAILTO=researcher@university.ac.id
```

### 2. Institutional / Subscription Pool
These sources require registered developer keys or campus IP token authentication:
- **Elsevier Scopus**: Requires `SCOPUS_API_KEY` and `SCOPUS_INSTTOKEN`.
- **Semantic Scholar Partner**: Requires `SEMANTIC_SCHOLAR_API_KEY`.
- **SINTA API**: Requires institutional endpoint configuration.

---

## ⚡ Fallback & Graceful Degradation Strategy

LiteraX will never fail completely if an institutional key expires or hits its monthly quota:
1. The aggregator marks the quota-exceeded provider as `INACTIVE_TEMPORARY`.
2. Queries continue executing against OpenAlex, Crossref, and Semantic Scholar.
3. User results include a badge indicating:
   `⚡ Results from OpenAlex, Crossref, Semantic Scholar (Scopus quota exceeded)`.
