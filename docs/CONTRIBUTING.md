# 🤝 Contributing to LiteraX

We love contributions from the open-source community! Whether it's adding a new academic data provider, improving fuzzy logic scoring, fixing bugs, or improving documentation, here's how you can help.

---

## 🛠️ Development Workflow

### 1. Fork & Branch
- Fork the repository on GitHub.
- Create a feature branch off `main`:
  ```bash
  git checkout -b feature/scopus-citation-enhancement
  ```

### 2. Setting Up Environment
Follow the instructions in [Development Guide](development/DEVELOPMENT.md):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Code Standards & Linting
Before committing code, ensure that all style checks pass:

```bash
# Format code
black .

# Check and auto-fix linter warnings
ruff check --fix .

# Static type checking
mypy src/
```

### 4. Running the Test Suite
Ensure that all existing tests pass and write new tests for your features:

```bash
pytest --cov=literax -v
```

---

## 💬 Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) convention:

- `feat(fuzzy)`: add Indonesian slang dictionary entries for computing terms
- `fix(scopus)`: handle 429 rate limit with exponential backoff
- `docs(api)`: add OpenAPI schema examples for /matrix endpoint
- `test(ranking)`: add unit test for composite relevance score formula
- `refactor(provider)`: migrate OpenAlex adapter to httpx connection pool

---

## ➕ Adding a New Provider Checklist

When submitting a PR that introduces a new academic database provider:
1. Subclass `literax.providers.base.ResearchProvider`.
2. Implement `search()` and `get_paper()` returning canonical `Paper` objects.
3. Add a dedicated integration doc in `docs/integrations/<NAME>.md`.
4. Include unit tests with mock HTTP responses in `tests/providers/test_<name>.py`.
5. Ensure graceful handling of timeout and missing metadata fields.

---

## 📬 Submitting a Pull Request
1. Push your branch to your fork.
2. Open a Pull Request against `main`.
3. Fill out the PR template with a description of the change, related issue numbers, and verification steps.
4. Maintainers will review your PR and provide constructive feedback.
