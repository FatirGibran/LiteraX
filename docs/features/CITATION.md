# 📖 Citation Generator

LiteraX generates bibliographic citations across all major scientific formats and machine-readable reference formats.

---

## 🏛️ Supported Citation Formats

### 1. Academic Publication Styles
- **APA 7th Edition**: Widely used in psychology, social sciences, and general computing.
- **IEEE**: Standard numerical format for engineering, computer science, and electrical fields.
- **Harvard**: Standard author-date style for academic institutions.
- **Vancouver**: Numbered bibliographic format utilized in medicine and life sciences.

### 2. Machine-Readable Formats
- **BibTeX (`.bib`)**: Native citation format for LaTeX, Overleaf, and Typst.
- **RIS (`.ris`)**: Tagged format supported by Zotero, Mendeley, EndNote, and JabRef.

---

## 📋 Citation Style Examples

Given the paper:
- **Title**: Machine Learning Approaches for Phishing URL Detection: An Empirical Study
- **Authors**: A. Rahman, S. Kumar
- **Journal**: Computers & Security
- **Volume**: 138, **Article**: 103982, **Year**: 2025
- **DOI**: `10.1016/j.cose.2024.103982`

### 1. APA 7th Edition
```text
Rahman, A., & Kumar, S. (2025). Machine learning approaches for phishing URL detection: An empirical study. Computers & Security, 138, Article 103982. https://doi.org/10.1016/j.cose.2024.103982
```

### 2. IEEE
```text
[1] A. Rahman and S. Kumar, "Machine learning approaches for phishing URL detection: An empirical study," Computers & Security, vol. 138, p. 103982, 2025, doi: 10.1016/j.cose.2024.103982.
```

### 3. Harvard
```text
Rahman, A. and Kumar, S., 2025. Machine learning approaches for phishing URL detection: An empirical study. Computers & Security, 138, p.103982.
```

### 4. BibTeX (`.bib`)
```bibtex
@article{rahman2025machine,
  title={Machine learning approaches for phishing URL detection: An empirical study},
  author={Rahman, A. and Kumar, S.},
  journal={Computers \& Security},
  volume={138},
  pages={103982},
  year={2025},
  publisher={Elsevier},
  doi={10.1016/j.cose.2024.103982}
}
```

### 5. RIS (`.ris`)
```text
TY  - JOUR
TI  - Machine learning approaches for phishing URL detection: An empirical study
AU  - Rahman, A.
AU  - Kumar, S.
JO  - Computers & Security
VL  - 138
SP  - 103982
PY  - 2025
DO  - 10.1016/j.cose.2024.103982
ER  - 
```

---

## ⚡ Crossref Content Negotiation

For papers indexed in Crossref, LiteraX uses **HTTP Content Negotiation** to pull authoritative citation strings directly from publishers:

```bash
# Requesting APA formatted text
curl -LH "Accept: text/x-bibliography; style=apa" https://doi.org/10.1016/j.cose.2024.103982

# Requesting raw BibTeX
curl -LH "Accept: application/x-bibtex" https://doi.org/10.1016/j.cose.2024.103982
```

This guarantees 100% fidelity without parsing errors.
