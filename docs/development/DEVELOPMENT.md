# 💻 Local Development Guide

This guide walks through setting up LiteraX for local development, executing test suites, configuring linters, and managing database migrations.

---

## 🛠️ Prerequisites

- **Python**: 3.12 or newer
- **PostgreSQL**: 16 with `pgvector` extension
- **Redis**: 7.x
- **Git**

---

## 📦 Setup Walkthrough

### 1. Clone & Virtual Environment

```bash
git clone https://github.com/fatirgibran/LiteraX.git
cd LiteraX

python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Development Dependencies

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### 3. Setup Local Services (Docker)

If you don't have local Postgres or Redis running, start them using docker compose:

```bash
docker compose up -d postgres redis
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Ensure `.env` contains:
```env
DATABASE_URL=postgresql+asyncpg://literax:literax_secret@localhost:5432/literax_db
REDIS_URL=redis://localhost:6379/0
OPENALEX_EMAIL=your.email@university.edu
CROSSREF_MAILTO=your.email@university.edu
LOG_LEVEL=DEBUG
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

---

## 🧪 Running Tests

LiteraX uses `pytest` and `pytest-asyncio` for unit and integration testing.

```bash
# Run all tests
pytest

# Run fuzzy auto-correct tests only
pytest tests/test_fuzzy_autocorrect.py -v

# Run provider mock tests
pytest tests/providers/ -v

# Run with test coverage
pytest --cov=literax --cov-report=term-missing
```

---

## 🎨 Code Style & Quality

LiteraX enforces formatting and linting rules using `ruff` and `black`:

```bash
# Check code style with ruff
ruff check .

# Automatically fix lint issues
ruff check --fix .

# Code formatting with black
black .

# Static type analysis with mypy
mypy src/
```

---

## 🚀 Running Applications Locally

### 1. Run FastAPI Gateway
```bash
uvicorn literax.api.main:app --reload --port 8000
```
Interactive Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Run Telegram Bot Worker
```bash
python -m literax.bot.main
```
