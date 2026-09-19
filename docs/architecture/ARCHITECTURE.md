# 🏗️ System Architecture

LiteraX is designed as a modular, layered, asynchronous platform capable of processing natural language academic queries, querying distributed academic providers, and synthesizing literature with AI.

---

## 📐 High-Level Architecture Diagram

```mermaid
graph TD
    Client[Client Interfaces<br>Telegram Bot / Web REST Client]
    
    subgraph GatewayLayer ["API & Interface Layer"]
        FastAPI[FastAPI Gateway<br>/search, /analyze, /matrix, /gap]
        Aiogram[aiogram v3 Bot Engine<br>Commands, Inline Buttons, FSM]
    end
    
    subgraph CoreEngine ["Query & Orchestration Layer"]
        QueryEngine[Query Processing Engine]
        FuzzyEngine[Fuzzy Logic Auto-Correct<br>RapidFuzz + Heuristic Scorer]
        ExpansionEngine[Academic Query Expander]
    end
    
    subgraph ProviderLayer ["Modular Provider Layer (Async Adapters)"]
        Aggregator[Paper Aggregator Pool]
        P_OpenAlex[OpenAlex Adapter]
        P_Scopus[Scopus Adapter]
        P_Crossref[Crossref Adapter]
        P_Semantic[Semantic Scholar Adapter]
        P_Sinta[SINTA / Garuda Adapter]
        P_Other[DOAJ / PubMed / arXiv]
    end
    
    subgraph SynthesisLayer ["Post-Processing & Synthesis Layer"]
        Dedup[Deduplication Engine<br>DOI + Levenshtein Title + Author]
        Ranker[Relevance Ranking Engine<br>BM25 + Semantic Cosine]
        AIEngine[AI Research Engine<br>LLM Parsing, Gap, Matrix]
    end
    
    subgraph StorageLayer ["Storage & Caching Layer"]
        Postgres[(PostgreSQL 16<br>Users, Papers, Sessions)]
        VectorDB[(pgvector<br>Paper Embeddings)]
        RedisCache[(Redis 7<br>Cache, Rate Limit, Sessions)]
    end

    Client --> FastAPI
    Client --> Aiogram
    FastAPI --> QueryEngine
    Aiogram --> QueryEngine
    
    QueryEngine --> FuzzyEngine
    FuzzyEngine --> QueryEngine
    QueryEngine --> ExpansionEngine
    
    ExpansionEngine --> Aggregator
    Aggregator --> P_OpenAlex
    Aggregator --> P_Scopus
    Aggregator --> P_Crossref
    Aggregator --> P_Semantic
    Aggregator --> P_Sinta
    Aggregator --> P_Other
    
    P_OpenAlex --> Aggregator
    P_Scopus --> Aggregator
    P_Crossref --> Aggregator
    P_Semantic --> Aggregator
    P_Sinta --> Aggregator
    P_Other --> Aggregator
    
    Aggregator --> Dedup
    Dedup --> Ranker
    Ranker --> AIEngine
    
    Ranker --> Postgres
    AIEngine --> Postgres
    Ranker --> VectorDB
    FastAPI <--> RedisCache
    Aiogram <--> RedisCache
```

---

## 🏛️ Layer Responsibilities

### 1. Interface & Gateway Layer
- **FastAPI**: Serves JSON APIs, handles JWT authentication, enforces rate limits, and coordinates long-running asynchronous jobs.
- **aiogram Bot**: Translates user chat interactions into backend commands, displays paginated search cards, and manages interactive feedback dialogues (e.g. asking confirmation for medium-confidence typos).

### 2. Query & Orchestration Layer
- **Normalization**: Strips non-academic punctuation, lowercases text, collapses whitespace, and preserves boolean operators (`AND`, `OR`, `NOT`).
- **Fuzzy Auto-Correct**: Analyzes tokens against curated academic and multilingual vocabularies (English and Indonesian). Uses multi-factor fuzzy logic scoring to produce candidate corrections with explainable confidence.
- **Query Expander**: Generates targeted synonyms, acronym expansions (e.g. `ML` $\leftrightarrow$ `Machine Learning`), and specialized queries for different database APIs.

### 3. Modular Provider Layer
- Implements the **Adapter Pattern**. Every academic database has a dedicated class inheriting from `ResearchProvider`.
- Search calls are executed in parallel via `asyncio.gather(..., return_exceptions=True)`.
- If an individual provider encounters a rate limit or network glitch, it fails gracefully without blocking other providers.

### 4. Post-Processing & Synthesis Layer
- **Deduplication Engine**: Merges duplicated papers indexed across multiple sources using canonical DOIs and high-precision string matching.
- **Relevance Ranker**: Evaluates search hits against the user's intent using a weighted composite of lexical matching, semantic vector similarity, publication year recency, and citation counts.
- **AI Research Engine**: Orchestrates LLMs to parse paper abstracts and PDFs into structured fields, build comparative matrices, and detect research gaps.

### 5. Persistence & Cache Layer
- **PostgreSQL 16**: Relational storage for users, search history, bibliographic records, and custom literature collections.
- **pgvector**: Stores high-dimensional paper embeddings for semantic similarity checks and paper recommendation.
- **Redis 7**: High-speed key-value store for caching external provider responses, managing bot pagination tokens, and rate limiting.

---

## 🔒 Design Decisions

1. **Async-First Throughout**: All provider interactions, database queries, and bot notifications run asynchronously to avoid blocking the main event loop during slow network calls.
2. **Strict Separation of Concerns**: Query correction is completely independent of search providers. This ensures typo correction can be unit-tested without network requests.
3. **Graceful Degradation**: If LLM services are temporarily unreachable, the search engine still delivers raw metadata, abstract excerpts, and direct links without crashing.
