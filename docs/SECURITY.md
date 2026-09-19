# 🔒 Security & Academic Integrity Policy

LiteraX adheres to strict ethical computing standards, API provider terms of service, and academic integrity policies.

---

## ⚠️ Academic Integrity & Ethical Use

LiteraX is designed strictly as an **educational and research assistant**.

### Permitted Uses:
- Rapid discovery and indexing of open-access and institutional scholarly works.
- Preliminary extraction of research methodologies, algorithms, datasets, and performance metrics.
- Generating draft citation strings in standard formats (APA, IEEE, BibTeX).
- Organizing personal reading lists and compiling literature review comparison matrices.

### Prohibited Uses:
- **No Paywall Bypassing**: LiteraX will never attempt to circumvent academic publisher paywalls or download pirated PDF documents.
- **No Citation Fabrication**: The system does not hallucinate fake citations or invent fictitious papers. Every citation must be anchored to an authentic provider DOI or registered identifier.
- **No Auto-Generated Plagiarism**: LLM syntheses and research gap observations are starting points that must be thoroughly validated, cited, and rewritten by the researcher.

---

## 🔑 Secret & Credential Management

1. **Never Commit Secrets**: Never push `.env` files, API tokens, or Telegram Bot keys into version control.
2. **Environment Variable Injection**: All credentials (`BOT_TOKEN`, `SCOPUS_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, `DATABASE_URL`) must be injected via runtime environment variables or secrets management solutions (e.g. Docker Secrets, HashiCorp Vault).
3. **Database Security**:
   - Connection strings in production must use SSL/TLS (`sslmode=require`).
   - PostgreSQL must be isolated within the internal Docker network and never exposed directly to public ports without firewall restrictions.

---

## 🛡️ Denial of Service & Abuse Mitigation

1. **Token-Bucket Rate Limiting**: Redis-backed rate limiting throttles abusive user sessions:
   - Max 20 searches per minute per user.
   - Max 5 AI extraction requests per minute per user.
2. **Input Sanitization**: User queries are stripped of malicious injection patterns before SQL queries or OS commands.
3. **Polite Crawling Compliance**: All scraper and crawler adapters enforce a minimum delay of 1.5 seconds between successive HTTP calls, accompanied by informative `User-Agent` contact headers.

---

## 🚨 Vulnerability Reporting

If you discover a security vulnerability within LiteraX, please do not open a public GitHub issue. Instead, report it privately to the maintainers at `security@literax.org` or create a GitHub Private Vulnerability Advisory.
