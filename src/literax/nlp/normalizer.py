import re
import unicodedata
from typing import List

class QueryNormalizer:
    """Handles unicode, whitespace, and punctuation normalization and tokenization."""

    BOOLEAN_OPERATORS = {"AND", "OR", "NOT"}

    @classmethod
    def normalize(cls, query: str) -> str:
        """Normalizes unicode, strips excess whitespace, and cleans punctuation."""
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
        text = re.sub(r"\s+", " ", text).strip()
        return text

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
