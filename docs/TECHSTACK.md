# 🛠️ Tech Stack & System Components

LiteraX is designed with a high-performance, asynchronous, modular Python architecture. Every module is loosely coupled, following **API-First**, **Async-First**, and **Provider-Agnostic** principles.

---

## 🏛️ High-Level Component Topology

```text
                    ┌───────────────────────────────┐
                    │      Clients & Interfaces     │
                    │   Telegram Bot  /  Web UI     │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │       FastAPI Gateway         │
                    │   Auth, Routing, Rate Limit   │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      Query & NLP Engine       │
                    │  RapidFuzz + Fuzzy Logic + AI │
                    └───────────────┬───────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
    │ Open Providers│       │ Subscribed API│       │ Local Vector  │
    │ OpenAlex/Cross│       │ Scopus/SINTA  │       │ pgvector / DB │
    └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │  Paper Aggregator & Ranker    │
                    │  Deduplication + Relevance    │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      AI Research Engine       │
                    │   Analysis, Gap, & Citation   │
                    └───────────────────────────────┘
```

---

## 💻 Technology Breakdown

### 1. 🐍 Core Language & Runtime
- **Language**: Python 3.12+
- **Rationale**: Python provides an unrivaled ecosystem for natural language processing, vector math, asynchronous web frameworks, and academic API clients.
- **Asynchronous Loop**: `asyncio` for non-blocking I/O across network calls.

### 2. 🤖 Telegram Bot Framework
- **Package**: `aiogram` (v3.x)
- **Rationale**: Modern, fully asynchronous Telegram bot framework built on `asyncio` and `pydantic`. Supports routers, filters, FSM (Finite State Machines), and inline pagination.
- **Key Responsibilities**:
  - Command handling (`/search`, `/analyze`, `/matrix`, `/gap`, `/cite`)
  - Inline query suggestions and callback buttons
  - Asynchronous progress notifications and file attachments (PDF/BibTeX)

### 3. 🌐 API Gateway & Web Server
- **Framework**: `FastAPI` + `Uvicorn`
- **Rationale**: Blazing fast ASGI server with native async support, automatic OpenAPI/Swagger documentation, and Pydantic-driven data validation.
- **Key Responsibilities**:
  - REST endpoints for query correction, search, paper extraction, and matrix compilation
  - Background task scheduling
  - Rate limiting and API security middleware

### 4. 🔤 Fuzzy Matching & Typo Correction
- **Primary Library**: `RapidFuzz` (C++ accelerated Levenshtein, Jaro-Winkler, Token Sort/Set Ratio)
- **Fuzzy Logic Scorer**: Custom Python fuzzy inference engine scoring five variables:
  1. String edit distance
  2. Academic vocabulary membership
  3. Context co-occurrence
  4. Global frequency score
  5. Query coherence score

### 5. 🔎 Academic Data Provider Layer
- **Async HTTP Client**: `httpx` (HTTP/2, connection pooling, backoff retry)
- **Providers**:
  - **OpenAlex API**: Global academic graph covering >250M works.
  - **Crossref REST API**: DOI metadata resolution and citation link parsing.
  - **Semantic Scholar API**: Contextual citation graphs and paper embeddings.
  - **Elsevier Scopus API**: High-impact peer-reviewed literature indexing.
  - **SINTA / GARUDA**: Indonesian accredited journals (S1 through S6).
  - **DOAJ, PubMed, arXiv, CORE**: Open access repositories.

### 6. 🧠 AI & LLM Orchestration
- **Model Providers**: Gemini 1.5 Pro / Flash, OpenAI GPT-4o / GPT-4o-mini, or Ollama (local models)
- **Responsibilities**:
  - Structured extraction of research problems, algorithms, metrics, and limitations
  - Cross-paper comparison for research gap hypothesis generation
  - Semantic query validation and multilingual translation

### 7. 🗄️ Database & Vector Storage
- **Relational Database**: `PostgreSQL 16`
- **Vector Search Extension**: `pgvector`
- **ORM & Migrations**: `SQLAlchemy 2.0` (async) + `Alembic`
- **Storage Scope**:
  - User accounts, search queries, and research sessions
  - Normalized paper metadata and author hierarchies
  - Document chunk embeddings (768 or 1536 dimensions) for semantic retrieval

### 8. ⚡ Caching & Session State
- **Store**: `Redis 7+`
- **Driver**: `redis-py` (`redis.asyncio`)
- **Use Cases**:
  - Query result caching (TTL: 24 hours) to minimize external API costs
  - Per-user rate limiting (token bucket algorithm)
  - Bot inline pagination states and multi-step dialog tracking

### 9. 📄 Document & PDF Extraction
- **PDF Engine**: `PyMuPDF` (`fitz`)
- **Rationale**: Significantly faster than PyPDF2 or pdfplumber, with superior text flow extraction, bounding box preservation, and metadata parsing.
- **Optional OCR Fallback**: `pytesseract` / Tesseract OCR for scanned PDF documents.

### 10. 🧪 Schema Validation & Serialization
- **Package**: `Pydantic v2`
- **Rationale**: Ultra-fast Rust-based data validation and JSON serialization. Ensures all incoming user payloads and provider responses conform strictly to predefined contracts.

---

## 📦 Recommended Dependency Specification (`pyproject.toml`)

```toml
[project]
name = "literax"
version = "0.1.0"
description = "AI-Powered Academic Research Automation Assistant"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    # API & Web
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.2.0",
    
    # Telegram Bot
    "aiogram>=3.7.0",
    
    # HTTP & Networking
    "httpx[http2]>=0.27.0",
    
    # Fuzzy & NLP
    "rapidfuzz>=3.9.0",
    "nltk>=3.8.1",
    
    # PDF & Document Processing
    "pymupdf>=1.24.0",
    
    # Database & Storage
    "sqlalchemy>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pgvector>=0.3.0",
    "redis>=5.0.4",
    
    # AI & Embeddings
    "google-generativeai>=0.7.0",
    "openai>=1.30.0",
    "tiktoken>=0.7.0",
    
    # Utilities
    "python-dotenv>=1.0.1",
    "loguru>=0.7.2",
    "tenacity>=8.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.0",
    "pytest-asyncio>=0.23.7",
    "ruff>=0.4.4",
    "black>=24.4.2",
    "mypy>=1.10.0",
    "httpx-mock>=0.3.0",
]
```

---

## 🧩 Architecture Principles

1. **Provider-Agnostic**: All academic engines inherit from an abstract base class `ResearchProvider`. Adding a new academic database requires zero changes to the core ranking and deduplication logic.
2. **Fail-Soft Isolation**: If one search provider times out or experiences an outage, other providers continue streaming results without crashing the overall query.
3. **Strict Validation**: All external API payloads are parsed through strict Pydantic schemas, preventing schema drift from corrupting the database.
4. **Transparent Explainability**: Every query correction provides a confidence score and diff showing changed tokens, giving researchers full visibility into algorithmic decisions.
