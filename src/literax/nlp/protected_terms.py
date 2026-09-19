import json
from pathlib import Path
from typing import Set

class ProtectedTermsManager:
    """Manages technical and scientific terms that must never be modified by auto-correct."""

    def __init__(self, dictionary_path: Path | None = None):
        if dictionary_path is None:
            dictionary_path = Path(__file__).parent / "dictionaries" / "protected_terms.json"
        
        self.protected_terms: Set[str] = set()
        if dictionary_path.exists():
            with open(dictionary_path, "r", encoding="utf-8") as f:
                terms = json.load(f)
                self.protected_terms = {t.lower() for t in terms}

    def is_protected(self, token: str) -> bool:
        """Returns True if the token is a protected scientific/technical term."""
        clean = token.lower().strip()
        # Direct check
        if clean in self.protected_terms:
            return True
        # Check hyphenated variations
        if clean.replace("-", "") in self.protected_terms:
            return True
        return False
