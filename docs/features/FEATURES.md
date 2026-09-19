# ✨ LiteraX Feature Catalog

This document provides a comprehensive overview of all features implemented in LiteraX.

---

## 📋 Feature Summary Matrix

| Feature | Description | Primary Technology | User Interface |
| :--- | :--- | :--- | :--- |
| **Fuzzy Auto-Correct** | Typo detection & correction with multi-factor confidence | RapidFuzz + Fuzzy Logic | Telegram & REST API |
| **Multi-Source Search** | Unified query across global & Indonesian academic indices | httpx + Async Adapters | `/search` command |
| **Query Expansion** | Enriches single queries with synonyms & booleans | AI / Rule-based NLP | Automated |
| **Paper Deduplication** | Merges duplicate publications across providers | DOI + String Distance | Automated |
| **Relevance Ranking** | Combines text match, vector similarity & citation counts | Custom Scorer / pgvector | Automated |
| **AI Paper Analysis** | Extracts methodology, datasets, findings, and limitations | LLM (Gemini / GPT) | `/analyze` button/command |
| **Research Gap Assistant** | Highlights unexplored algorithm/dataset combinations | LLM Cross-Paper Analysis | `/gap` command |
| **Literature Matrix** | Formats multiple papers into a structured matrix table | Markdown / CSV Export | `/matrix` command |
| **Citation Generator** | Generates citations in APA, IEEE, Harvard, BibTeX, RIS | Citation Engine | `/cite` button/command |

---

## 🔬 In-Depth Feature Descriptions

### 1. Multi-Source Academic Search
Users can retrieve literature across both global indexing engines and Indonesian national indices. Search requests can be filtered by:
- Publication Year range (`year_start`, `year_end`)
- Open Access status (`open_access_only=True`)
- Source specific routing (e.g. searching only Scopus or SINTA)

### 2. Fuzzy Logic Auto-Correct
Corrects spelling mistakes without destroying technical terminology.
- Supports bilingual inputs (Bahasa Indonesia & English).
- Distinguishes high-confidence auto-fixes from ambiguous cases requiring user confirmation.
- Protects technical acronyms (`CNN`, `SVM`, `BERT`, `LSTM`, `IoT`).

### 3. Query Expansion & Translation
Automatically translates queries to optimize search recall:
- User input: `deteksi phising dengan machine learning`
- Expanded queries:
  - `"phishing detection" AND "machine learning"`
  - `"phishing website classification" AND "deep learning"`
  - `"phishing URL detection" AND "random forest"`

### 4. Paper Deduplication
Academic literature often appears simultaneously in Crossref, OpenAlex, and Scopus. LiteraX cleanses this by:
- Normalizing DOI strings (e.g. `https://doi.org/10.1016/...` $\rightarrow$ `10.1016/...`).
- Performing fuzzy title matching for papers without DOIs.
- Preserving the richest metadata from across conflicting source records.

### 5. Automated Paper Analysis
Transforms long academic PDFs and abstracts into high-density structured summaries:
- **Research Problem**: The exact issue or vulnerability addressed.
- **Proposed Methodology**: Models, algorithms, or theoretical frameworks utilized.
- **Dataset Details**: Name, volume, collection timeframe, and feature set.
- **Evaluation & Metrics**: F1-score, accuracy, precision, AUC-ROC, latency.
- **Key Limitations**: Flaws, computational bottlenecks, or domain constraints acknowledged by the authors.

### 6. Research Gap Discovery
By analyzing a cluster of papers on a topic, LiteraX identifies patterns in methodologies and datasets, identifying:
- Inconsistent experimental baselines.
- Algorithms tested only on legacy or synthetic datasets.
- Missing comparative benchmarks between traditional ML and recent deep architectures.

### 7. Interactive Telegram Interface
Provides a frictionless mobile and desktop interface via Telegram:
- Interactive pagination (Next / Prev buttons).
- One-click buttons to download full-text PDFs, copy citations, or request deep AI breakdowns.
- User library management (`/save`, `/saved`) to compile papers into personal research sessions.
