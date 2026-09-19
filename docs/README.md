# 📚 LiteraX Documentation Portal

Welcome to the documentation portal for **LiteraX (Research Automation Bot)**. This site covers architecture, algorithms, provider integrations, API references, database schemas, and deployment instructions.

---

## 🗺️ Documentation Structure

```text
docs/
├── README.md                      # Documentation Index (this file)
├── TECHSTACK.md                   # Core technology stack and libraries
├── SECURITY.md                    # Academic integrity, API key protection, security guidelines
├── ROADMAP.md                     # Development roadmap (v0.1 to v2.0)
├── CONTRIBUTING.md                # Contribution standards, git workflow, linting
│
├── architecture/
│   ├── ARCHITECTURE.md            # System architecture and module breakdown
│   ├── DATA-FLOW.md               # End-to-end data pipeline from query to matrix
│   └── PROVIDER-ARCHITECTURE.md   # Modular provider interface and adapter pattern
│
├── features/
│   ├── FEATURES.md                # Feature overview and matrix
│   ├── FUZZY-AUTOCORRECT.md       # Fuzzy logic auto-correct, RapidFuzz, confidence equations
│   ├── SEARCH-ENGINE.md           # Query expansion, deduplication, and ranking engine
│   ├── PAPER-ANALYSIS.md          # AI-powered document extraction and breakdown
│   ├── RESEARCH-GAP.md            # Automated methodology comparison and research gap detection
│   ├── LITERATURE-MATRIX.md       # Synthesis matrix generator and tabular exports
│   └── CITATION.md                # Citation generation (APA, IEEE, Harvard, BibTeX, RIS)
│
├── integrations/
│   ├── DATA-SOURCES.md            # Academic database directory and provider matrix
│   ├── SINTA.md                   # Indonesian SINTA indexing and integration
│   ├── SCOPUS.md                  # Elsevier Scopus API setup and tokens
│   ├── OPENALEX.md                # OpenAlex API entities and polite pool
│   ├── CROSSREF.md                # Crossref REST API and DOI resolution
│   └── SEMANTIC-SCHOLAR.md        # Semantic Scholar Graph API and citations
│
└── development/
    ├── DEVELOPMENT.md             # Developer setup, testing, and toolchain
    ├── API.md                     # FastAPI REST API specification and models
    ├── DATABASE.md                # PostgreSQL schema, ERD, and pgvector embeddings
    ├── TELEGRAM-BOT.md            # aiogram v3 architecture, commands, and keyboards
    └── DEPLOYMENT.md              # Docker, Docker Compose, Nginx, and production setup
```

---

## 🧭 Navigation Guides

### 1. Understanding the Core Concept
If you want to understand how LiteraX corrects user queries and retrieves papers:
- Start with [Fuzzy Auto-Correct](features/FUZZY-AUTOCORRECT.md) to see how typos like `machin lerning untk deteksi phising` are normalized and assigned confidence scores.
- Read [Data Flow Pipeline](architecture/DATA-FLOW.md) to inspect the 10-stage processing sequence.
- Explore the [Search Engine](features/SEARCH-ENGINE.md) to learn how deduplication and relevance ranking work.

### 2. Working on Integrations
If you are adding or debugging academic data sources:
- Review [Provider Architecture](architecture/PROVIDER-ARCHITECTURE.md) for the `ResearchProvider` abstract base class.
- Read [Data Sources Overview](integrations/DATA-SOURCES.md) and individual provider specs:
  - [OpenAlex](integrations/OPENALEX.md) (Open Access, fast, broad metadata)
  - [Elsevier Scopus](integrations/SCOPUS.md) (Indexed literature, requires API Key & InstToken)
  - [SINTA](integrations/SINTA.md) (Indonesian national accredited journals S1-S6)
  - [Crossref](integrations/CROSSREF.md) (DOI registry and citation graphs)
  - [Semantic Scholar](integrations/SEMANTIC-SCHOLAR.md) (AI-powered academic graph)

### 3. Developing and Extending LiteraX
If you are writing code or running the project locally:
- Follow the [Development Guide](development/DEVELOPMENT.md) to set up your environment.
- Check the [FastAPI REST API Reference](development/API.md) for endpoints and schemas.
- Inspect the [Database Guide](development/DATABASE.md) for PostgreSQL and pgvector configurations.
- Read the [Telegram Bot Guide](development/TELEGRAM-BOT.md) for interaction workflows.

### 4. Deploying to Production
- Refer to [Deployment Guide](development/DEPLOYMENT.md) for Docker Compose and Nginx configurations.
- Review [Security Guidelines](SECURITY.md) to safeguard credentials and respect API rate limits.
