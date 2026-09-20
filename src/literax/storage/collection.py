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
        if self.persistence_file and self.persistence_file.exists():
            self._load_from_disk()


    def _load_from_disk(self) -> None:
        try:
            with open(self.persistence_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                for user_id, paper_dicts in raw_data.items():
                    self._collections[user_id] = [Paper.model_validate(p) for p in paper_dicts]
        except Exception:
            pass

    def _save_to_disk(self) -> None:
        if not self.persistence_file:
            return
        try:
            self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
            serializable = {
                uid: [p.model_dump() for p in papers]
                for uid, papers in self._collections.items()
            }
            with open(self.persistence_file, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2)
        except Exception:
            pass

    def add_paper(self, user_id: str, paper: Paper) -> bool:
        """Adds a paper to user's collection. Returns True if added, False if already present."""
        if user_id not in self._collections:
            self._collections[user_id] = []

        existing_papers = self._collections[user_id]
        for ep in existing_papers:
            if ep.id == paper.id or (paper.doi and ep.doi and paper.doi.lower() == ep.doi.lower()):
                return False

        self._collections[user_id].append(paper)
        self._save_to_disk()
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
            self._save_to_disk()

    def count(self, user_id: str) -> int:
        """Returns total number of papers saved by a user."""
        return len(self._collections.get(user_id, []))
