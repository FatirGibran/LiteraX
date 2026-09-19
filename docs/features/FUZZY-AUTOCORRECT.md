# 🧠 Fuzzy Logic Auto-Correct Engine

The **Fuzzy Logic Auto-Correct Engine** is LiteraX's query preprocessing module. It detects typos, spelling errors, colloquial abbreviations, and bilingual syntax before queries reach academic search providers.

---

## 🎯 The Academic Typo Challenge

Standard typo-correction libraries often fail when handling academic search queries because:
1. Academic vocabularies contain specialized terminology (`adversarial`, `hyperparameter`, `stochastic`).
2. Indonesian and English terms are frequently mixed in a single query (e.g. `deteksi phishing menggunakan machine learning`).
3. Many acronyms (`SVM`, `BERT`, `LLM`, `IoT`, `GAN`) have small edit distances from common words (`SUM`, `BEST`, `ALL`, `NOT`, `MAN`) and must never be "corrected".

LiteraX resolves this by pairing **RapidFuzz** string similarity with a multi-factor **Fuzzy Logic Confidence Engine**.

---

## 🔄 Correction Pipeline

```text
User Input: "machin lerning untk deteksi phising"
    │
    ▼
1. Normalization (Lowercase, whitespace collapse, punctuation clean)
    │
    ▼
2. Tokenization & Protected Term Filtering
    │
    ▼
3. Dictionary Lookup & Candidate Generation (RapidFuzz)
    │
    ▼
4. Multi-Factor Fuzzy Logic Scoring
    │
    ▼
5. Confidence Decision
    ├── HIGH (C >= 0.90)  ──> Auto-Apply Correction
    ├── MEDIUM (0.70 <= C < 0.90) ──> Prompt Confirmation to User
    └── LOW (C < 0.70)   ──> Retain Original Token
```

---

## 🧮 Fuzzy Logic Confidence Calculation

The system computes confidence $C \in [0.0, 1.0]$ for each token candidate:

$$C = w_1 S_{\text{string}} + w_2 V_{\text{academic}} + w_3 S_{\text{context}} + w_4 F_{\text{freq}} + w_5 Q_{\text{coherence}}$$

### Default Weights Configuration:
- $w_1 = 0.40$ — **String Similarity** ($S_{\text{string}}$): Levenshtein & Jaro-Winkler ratio.
- $w_2 = 0.20$ — **Academic Vocabulary Match** ($V_{\text{academic}}$): $1.0$ if present in curated scientific corpora, else $0.5$.
- $w_3 = 0.20$ — **Context Similarity** ($S_{\text{context}}$): Semantic co-occurrence score with adjacent query words.
- $w_4 = 0.10$ — **Frequency Score** ($F_{\text{freq}}$): Corpus term frequency weight.
- $w_5 = 0.10$ — **Query Coherence** ($Q_{\text{coherence}}$): Bigram/trigram likelihood in scientific literature.

---

## 🚦 Decision Thresholds

| Confidence Level | Score Range | System Action | Example Flow |
| :--- | :--- | :--- | :--- |
| **HIGH** | $0.90 \le C \le 1.00$ | Automatically corrects the query and informs the user. | `machne lerning` $\rightarrow$ `machine learning` (Conf: 96%) |
| **MEDIUM** | $0.70 \le C < 0.90$ | Retains query but renders inline confirmation buttons. | `did you mean: cyber security? [Yes] [Keep Original]` |
| **LOW** | $C < 0.70$ | Leaves text unchanged; avoids distortion. | Rare author surnames or obscure acronyms |

---

## 🛡️ Protected Terms (Do Not Correct)

LiteraX maintains an immutable dictionary of technical acronyms and domain keywords that are exempt from fuzzy distance corrections:

```json
[
  "SVM", "CNN", "RNN", "LSTM", "GAN", "BERT", "GPT", "LLM", "NLP",
  "XGBoost", "AdaBoost", "PCA", "t-SNE", "KNN", "DBSCAN",
  "IoT", "5G", "6G", "RFID", "UAV", "WSN", "API", "REST",
  "COVID-19", "SARS", "DNA", "RNA", "CRISPR"
]
```

Any token matching a protected term is immediately assigned a bypass flag.

---

## 🌎 Vocabulary Dictionaries

The engine bundles structured vocabulary databases located in `src/literax/nlp/dictionaries/`:

- `academic_terms_en.json`: >35,000 English academic, computational, and biomedical terms.
- `academic_terms_id.json`: >15,000 Indonesian academic and colloquial mapping entries (e.g. `untk` $\rightarrow$ `untuk`, `menggunkan` $\rightarrow$ `menggunakan`).
- `domain_taxonomies/`: Domain-specific lexicons (`cybersecurity.json`, `artificial_intelligence.json`, `healthcare.json`).

### Example Dictionary Mapping

```json
{
  "phising": "phishing",
  "machne": "machine",
  "lerning": "learning",
  "artifical": "artificial",
  "inteligence": "intelligence",
  "klasifikasi": "klasifikasi",
  "akurasi": "akurasi",
  "jaringan": "jaringan"
}
```

---

## 📊 Structured Correction Object

Every correction generates a structured object returned by the API and logged to the session:

```json
{
  "original_query": "deteksi phising menggunkan machne lerning",
  "corrected_query": "deteksi phishing menggunakan machine learning",
  "overall_confidence": 0.954,
  "action_taken": "AUTO_CORRECTED",
  "tokens": [
    {
      "original": "deteksi",
      "corrected": "deteksi",
      "status": "UNCHANGED",
      "confidence": 1.0
    },
    {
      "original": "phising",
      "corrected": "phishing",
      "status": "CORRECTED",
      "confidence": 0.98,
      "distance_metric": "Levenshtein(1)"
    },
    {
      "original": "menggunkan",
      "corrected": "menggunakan",
      "status": "CORRECTED",
      "confidence": 0.93,
      "distance_metric": "Levenshtein(1)"
    },
    {
      "original": "machne",
      "corrected": "machine",
      "status": "CORRECTED",
      "confidence": 0.95,
      "distance_metric": "Levenshtein(1)"
    },
    {
      "original": "lerning",
      "corrected": "learning",
      "status": "CORRECTED",
      "confidence": 0.96,
      "distance_metric": "Levenshtein(1)"
    }
  ]
}
```

---

## 🧪 Implementation Example

```python
from rapidfuzz import process, fuzz
from typing import Dict, Any

class FuzzyAutoCorrect:
    def __init__(self, vocab: set, protected_terms: set):
        self.vocab = vocab
        self.protected_terms = {t.lower() for t in protected_terms}

    def calculate_confidence(self, token: str, candidate: str) -> float:
        s_string = fuzz.ratio(token, candidate) / 100.0
        v_academic = 1.0 if candidate in self.vocab else 0.5
        s_context = 0.95  # Evaluated from n-gram coherence
        f_freq = 0.90
        q_coherence = 0.95
        
        confidence = (
            0.40 * s_string +
            0.20 * v_academic +
            0.20 * s_context +
            0.10 * f_freq +
            0.10 * q_coherence
        )
        return round(confidence, 3)

    def correct_token(self, token: str) -> Dict[str, Any]:
        token_clean = token.strip().lower()
        if token_clean in self.protected_terms or token_clean in self.vocab:
            return {"original": token, "corrected": token, "confidence": 1.0}

        match = process.extractOne(token_clean, self.vocab, scorer=fuzz.ratio)
        if not match:
            return {"original": token, "corrected": token, "confidence": 0.0}

        best_candidate, _, _ = match
        conf = self.calculate_confidence(token_clean, best_candidate)

        if conf >= 0.90:
            return {"original": token, "corrected": best_candidate, "confidence": conf}
        return {"original": token, "corrected": token, "confidence": conf}
```
