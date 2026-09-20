import io
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
from literax.models import Paper
from literax.synthesis.citation import CitationGenerator

class PaperCollectionManager:
    """Manages persistent personal paper collections, bookmarks, and formatted exports."""

    def __init__(self, persistence_file: Optional[Path] = None):
        self.persistence_file = persistence_file
        self._collections: Dict[str, List[Paper]] = {}

    def add_paper(self, user_id: str, paper: Paper) -> bool:
        """Adds a paper to user's collection. Returns True if added, False if already present."""
        if user_id not in self._collections:
            self._collections[user_id] = []

        existing_papers = self._collections[user_id]
        for ep in existing_papers:
            if ep.id == paper.id or (paper.doi and ep.doi and paper.doi.lower() == ep.doi.lower()):
                return False

        self._collections[user_id].append(paper)
        return True

    def get_papers(self, user_id: str) -> List[Paper]:
        """Returns list of papers saved by the user."""
        return self._collections.get(user_id, []).copy()

    def remove_paper(self, user_id: str, paper_id: str) -> bool:
        """Removes a paper by ID or DOI. Returns True if removed, False otherwise."""
        if user_id not in self._collections:
            return False

        orig_len = len(self._collections[user_id])
        self._collections[user_id] = [
            p for p in self._collections[user_id]
            if p.id != paper_id and p.doi != paper_id
        ]
        return len(self._collections[user_id]) < orig_len

    def clear_collection(self, user_id: str) -> None:
        """Clears all saved papers for a user."""
        if user_id in self._collections:
            del self._collections[user_id]

    def count(self, user_id: str) -> int:
        """Returns total number of papers saved by a user."""
        return len(self._collections.get(user_id, []))
