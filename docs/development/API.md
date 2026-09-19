# 🌐 REST API Specification

LiteraX provides a FastAPI REST API for integration with web dashboards, browser extensions, and external pipelines.

---

## 📌 Base URL
```text
http://localhost:8000/api/v1
```

---

## 📑 Endpoints Summary

| Method | Path | Summary | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/correct` | Fuzzy auto-correct & confidence score | Optional |
| `POST` | `/search` | Multi-source academic literature search | Optional |
| `POST` | `/analyze` | Extract structured analysis from paper/PDF | Optional |
| `POST` | `/matrix` | Compile literature review matrix table | Yes |
| `POST` | `/gap` | Discover research gaps from paper cluster | Yes |
| `GET` | `/papers/{id}/citation` | Retrieve formatted citation (APA, IEEE, BibTeX) | Optional |

---

## 🔬 Detailed Endpoint Specifications

### 1. Auto-Correct Query
`POST /api/v1/correct`

#### Request Payload
```json
{
  "query": "machin lerning untk deteksi phising"
}
```

#### Response Payload (200 OK)
```json
{
  "original_query": "machin lerning untk deteksi phising",
  "corrected_query": "machine learning untuk deteksi phishing",
  "confidence": 0.954,
  "action": "AUTO_CORRECTED",
  "tokens": [
    {"original": "machin", "corrected": "machine", "score": 0.94},
    {"original": "lerning", "corrected": "learning", "score": 0.96},
    {"original": "untk", "corrected": "untuk", "score": 0.92},
    {"original": "deteksi", "corrected": "deteksi", "score": 1.0},
    {"original": "phising", "corrected": "phishing", "score": 0.98}
  ]
}
```

---

### 2. Multi-Source Search
`POST /api/v1/search`

#### Request Payload
```json
{
  "query": "machine learning phishing detection",
  "providers": ["openalex", "scopus", "crossref", "semanticscholar"],
  "year_start": 2022,
  "year_end": 2025,
  "limit": 10,
  "open_access_only": false
}
```

#### Response Payload (200 OK)
```json
{
  "total_found": 42,
  "returned_count": 10,
  "papers": [
    {
      "id": "10.1016/j.cose.2024.103982",
      "title": "Machine Learning Approaches for Phishing URL Detection: An Empirical Study",
      "abstract": "Phishing attacks represent a pervasive threat...",
      "doi": "10.1016/j.cose.2024.103982",
      "year": 2025,
      "authors": ["A. Rahman", "S. Kumar"],
      "journal": "Computers & Security",
      "citation_count": 34,
      "source": "Scopus",
      "open_access": true,
      "full_text_url": "https://example.com/fulltext.pdf",
      "composite_relevance": 0.96
    }
  ]
}
```

---

### 3. Paper Analysis
`POST /api/v1/analyze`

#### Request Payload
```json
{
  "paper_id": "10.1016/j.cose.2024.103982",
  "extract_depth": "deep"
}
```

#### Response Payload (200 OK)
```json
{
  "title": "Machine Learning Approaches for Phishing URL Detection: An Empirical Study",
  "problem_statement": "Rapid evolution of zero-day phishing websites evades conventional blacklists.",
  "research_objective": "Benchmark traditional classifiers against transformer architectures.",
  "methodology": "Lexical feature engineering combined with BERT tokenization.",
  "dataset": "PhishTank and UNB Phishing 2023 (120,000 samples).",
  "algorithms_used": ["Random Forest", "XGBoost", "DistilBERT"],
  "evaluation_metrics": ["Accuracy", "F1-Score", "FPR"],
  "key_findings": "DistilBERT achieved 98.4% accuracy with 0.8% FPR.",
  "limitations": "High computational latency of BERT (45ms per URL).",
  "future_work": "Model quantization for real-time edge firewall deployment."
}
```

---

### 4. Citation Generation
`GET /api/v1/papers/{id}/citation?style=apa`

#### Query Parameters:
- `style`: `apa` | `ieee` | `harvard` | `vancouver` | `bibtex` | `ris`

#### Response Payload (200 OK)
```json
{
  "style": "apa",
  "citation": "Rahman, A., & Kumar, S. (2025). Machine learning approaches for phishing URL detection: An empirical study. Computers & Security, 138, 103982. https://doi.org/10.1016/j.cose.2024.103982"
}
```
