# 🔄 End-to-End Data Flow

This document details the complete end-to-end data processing pipeline of LiteraX, from a user's initial misspelled raw query through to the synthesis of research gaps and literature matrices.

---

## 📈 10-Stage Pipeline Overview

```text
Raw Query
   │  ("machin lerning untk deteksi phising")
   ▼
[Stage 1: Normalization]
   │  ("machine lerning untk deteksi phising")
   ▼
[Stage 2: Tokenization]
   │  (["machine", "lerning", "untk", "deteksi", "phising"])
   ▼
[Stage 3: Fuzzy Matching]
   │  (Candidates: "learning", "untuk", "phishing")
   ▼
[Stage 4: Fuzzy Logic Confidence Calculation]
   │  (Compute C = 0.95 -> HIGH Confidence)
   ▼
[Stage 5: Candidate Correction & Diff Assembly]
   │  ("machine learning untuk deteksi phishing")
   ▼
[Stage 6: Semantic Validation & Protected Term Check]
   │  (Confirm context integrity; preserve terms like SVM, BERT)
   ▼
[Stage 7: Search Expansion]
   │  (Generate boolean & translated academic variants)
   ▼
[Stage 8: Multi-Source Concurrent Search]
   │  (Fan-out to OpenAlex, Scopus, Semantic Scholar, Crossref, SINTA)
   ▼
[Stage 9: Deduplication & Relevance Ranking]
   │  (Merge DOI collisions, compute multi-factor relevance scores)
   ▼
[Stage 10: AI Paper Synthesis & Output Generation]
      (Structured analysis, matrix table, research gap, citation export)
```

---

## 🔍 Detailed Pipeline Breakdown

### Stage 1: Raw Query Normalization
- **Goal**: Clean dirty raw user text without removing semantic operators.
- **Operations**:
  - Strip surrounding whitespace and consecutive spaces (`\s+` $\rightarrow$ single space).
  - Normalize unicode characters (NFKC normalization).
  - Lowercase all characters except boolean keywords (`AND`, `OR`, `NOT`).
  - Strip punctuation while preserving hyphens within compounds (e.g. `deep-learning`, `covid-19`).

### Stage 2: Tokenization
- **Goal**: Break normalized query into processable grammatical and terminological tokens.
- **Operations**:
  - Token split based on whitespace and boundary punctuation.
  - Multi-word term grouping using an n-gram sliding window (e.g., detecting `neural network` as a single semantic entity).
  - Identification of technical stop words.

### Stage 3: Fuzzy Matching
- **Goal**: Identify candidate corrections for words not found in the standard dictionary.
- **Operations**:
  - Tokens are checked against:
    1. English academic vocabulary (`academic_terms_en.json`)
    2. Indonesian academic vocabulary (`academic_terms_id.json`)
    3. Technical domain taxonomy (AI, cybersecurity, medicine, physics).
  - For unknown tokens, `RapidFuzz` computes similarity ratios against candidate terms:
    - Levenshtein distance
    - Jaro-Winkler distance
    - Token Set Ratio

### Stage 4: Fuzzy Logic Confidence Calculation
- **Goal**: Assign an objective, explainable confidence score $C \in [0.0, 1.0]$ to each proposed replacement.
- **Formula**:
  $$C = 0.40 \cdot S_{\text{string}} + 0.20 \cdot V_{\text{academic}} + 0.20 \cdot S_{\text{context}} + 0.10 \cdot F_{\text{freq}} + 0.10 \cdot Q_{\text{coherence}}$$
- **Confidence Decision**:
  - $C \ge 0.90$ (**HIGH**): Automatically apply correction.
  - $0.70 \le C < 0.90$ (**MEDIUM**): Ask user for confirmation via interactive buttons.
  - $C < 0.70$ (**LOW**): Keep original term to avoid distortion.

### Stage 5: Candidate Correction & Diff Assembly
- **Goal**: Build the corrected query string while preserving user intent and tracking modifications.
- **Output Structure**:
  ```json
  {
    "original": "machin lerning untk deteksi phising",
    "corrected": "machine learning untuk deteksi phishing",
    "confidence": 0.95,
    "tokens_changed": [
      {"from": "machin", "to": "machine", "score": 0.94},
      {"from": "lerning", "to": "learning", "score": 0.96},
      {"from": "untk", "to": "untuk", "score": 0.92},
      {"from": "phising", "to": "phishing", "score": 0.98}
    ]
  }
  ```

### Stage 6: Semantic Validation & Protected Term Check
- **Goal**: Ensure the correction did not drift away from the user's domain.
- **Operations**:
  - Protected term verification: Ensures acronyms like `SVM`, `CNN`, `BERT`, `LLM`, `IoT`, `5G` are never modified by mistake.
  - Cosine similarity verification between original and corrected query embeddings. If semantic similarity drops below a threshold, the system flags the correction.

### Stage 7: Search Expansion
- **Goal**: Maximize recall across diverse academic databases.
- **Operations**:
  - Translate Indonesian queries to English equivalents when querying international databases (e.g. Scopus, OpenAlex).
  - Generate synonym-enriched variations:
    - `"machine learning" phishing detection`
    - `"deep learning" phishing website detection`
    - `"phishing URL classification" machine learning`

### Stage 8: Multi-Source Concurrent Search
- **Goal**: Query multiple academic providers in parallel without blocking.
- **Operations**:
  - Asynchronously dispatch HTTP requests via `httpx` to OpenAlex, Scopus, Crossref, Semantic Scholar, and SINTA.
  - Enforce timeout bounds (e.g., 5.0 seconds per provider) with exponential backoff for transient failures.

### Stage 9: Deduplication & Relevance Ranking
- **Goal**: Eliminate redundant papers and order results by academic relevance.
- **Operations**:
  - **Deduplication**: Match papers by normalized DOI. For papers lacking DOIs, match by fuzzy title distance (Levenshtein ratio $> 0.88$) combined with author name and publication year match.
  - **Ranking**: Combine lexical keyword match, abstract vector cosine similarity, publication recency, and citation counts.

### Stage 10: AI Paper Synthesis & Output Generation
- **Goal**: Provide actionable insights to the researcher.
- **Operations**:
  - Generate structured paper summaries (Problem, Objective, Method, Dataset, Metrics, Limitations).
  - Build cross-paper literature matrices.
  - Formulate potential research gaps based on methodological differences.
  - Export citations in APA, IEEE, BibTeX, and RIS formats.

---

## 🏛️ Component Architecture Mapping

```text
[Telegram Bot / REST API Client]
       │
       ├── /search, /correct ──► [NLP Fuzzy Engine & Normalizer]
       │                               │
       │                               ▼
       ├── Multi-Source Search ─► [PaperAggregator]
       │                               ├── [CrossrefProvider]
       │                               ├── [OpenAlexProvider]
       │                               └── [ScopusProvider]
       │                                       │
       │                                       ▼
       │                          [Title & DOI Deduplicator]
       │                                       │
       │                                       ▼
       ├── Synthesis ──────────► [PaperAnalyzer / MatrixBuilder / GapFinder]
       │                                       │
       │                                       ▼
       └── Bookmarks ──────────► [PaperCollectionManager (JSON / Disk)]
```

