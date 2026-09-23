import re
import unicodedata
from typing import List

class QueryNormalizer:
    """Handles unicode, whitespace, and punctuation normalization and tokenization."""

    BOOLEAN_OPERATORS = {"AND", "OR", "NOT"}

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Collapses consecutive whitespace characters into a single space and strips boundaries."""
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def normalize(cls, query: str) -> str:
        """Normalizes unicode characters (NFKC), strips excess whitespace, and cleans punctuation."""
        if not query:
            return ""

        # Unicode NFKC normalization
        text = unicodedata.normalize("NFKC", query)

        # Preserve hyphens within words (e.g. f1-score, deep-learning, covid-19)
        # Replace other punctuation with space
        cleaned_chars = []
        for i, char in enumerate(text):
            if char.isalnum() or char.isspace():
                cleaned_chars.append(char)
            elif char == "-" and 0 < i < len(text) - 1 and text[i-1].isalnum() and text[i+1].isalnum():
                cleaned_chars.append(char)
            elif char in {'"', "'"}:
                # Keep quotes for exact phrases
                cleaned_chars.append(char)
            else:
                cleaned_chars.append(" ")

        text = "".join(cleaned_chars)

        # Collapse whitespace
        return cls.clean_whitespace(text)

    @classmethod
    def tokenize(cls, normalized_query: str) -> List[str]:
        """Splits normalized query into tokens."""
        if not normalized_query:
            return []
        
        raw_tokens = normalized_query.split(" ")
        tokens = []
        for token in raw_tokens:
            cleaned = token.strip("\"'.,;:")
            if cleaned:
                tokens.append(cleaned)
        return tokens

    @classmethod
    def extract_filters(cls, query: str) -> tuple[str, dict]:
        """Extracts provider, open-access, and year filter prefixes from user query.

        Examples:
        - "scopus: machine learning" -> ("machine learning", {"providers": ["scopus"]})
        - "sinta: sistem pakar" -> ("sistem pakar", {"providers": ["sinta"]})
        - "oa: deep learning" -> ("deep learning", {"open_access_only": True})
        - "year:2024 blockchain" -> ("blockchain", {"year_start": 2024})
        """
        if not query:
            return "", {}

        clean_text = query.strip()
        filters: dict = {}

        # 1. Provider / Index filter (e.g. scopus:, sinta:, garuda:, source:scopus)
        provider_match = re.search(
            r"\b(?:provider|source|indeks|index|db):\s*([a-zA-Z0-9_\-]+)\b|\b(scopus|sinta|garuda|openalex|crossref|semanticscholar):\s*",
            clean_text,
            flags=re.IGNORECASE
        )
        if provider_match:
            p_val = (provider_match.group(1) or provider_match.group(2)).lower()
            if p_val in ["garuda", "sinta"]:
                filters["providers"] = ["sinta"]
            else:
                filters["providers"] = [p_val]
            clean_text = clean_text[:provider_match.start()] + " " + clean_text[provider_match.end():]

        # 2. Open Access filter (e.g. oa:, openaccess:)
        oa_match = re.search(
            r"\b(oa|openaccess|open-access):\s*|\b(?:access):\s*(open|oa)\b",
            clean_text,
            flags=re.IGNORECASE
        )
        if oa_match:
            filters["open_access_only"] = True
            clean_text = clean_text[:oa_match.start()] + " " + clean_text[oa_match.end():]

        # 3. Year filter (e.g. year:2024, tahun:2024)
        year_match = re.search(
            r"\b(?:year|tahun|thn):\s*(\d{4})\b",
            clean_text,
            flags=re.IGNORECASE
        )
        if year_match:
            filters["year_start"] = int(year_match.group(1))
            clean_text = clean_text[:year_match.start()] + " " + clean_text[year_match.end():]

        clean_query = cls.clean_whitespace(clean_text)
        return clean_query, filters
