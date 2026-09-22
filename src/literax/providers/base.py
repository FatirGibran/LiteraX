from abc import ABC, abstractmethod
from typing import List, Optional
from literax.models import Paper, SearchQuery

class ResearchProvider(ABC):
    """Abstract Base Class for all academic data providers."""

    name: str
    requires_auth: bool = False
    timeout: float = 10.0

    @property
    def is_authenticated(self) -> bool:
        """Returns True if the provider has all required credentials configured."""
        return not self.requires_auth

    @abstractmethod
    async def search(self, query: SearchQuery) -> List[Paper]:
        """Searches the academic data source and returns normalized papers."""
        raise NotImplementedError

    @abstractmethod
    async def get_paper(self, identifier: str) -> Optional[Paper]:
        """Fetches metadata for a single paper by DOI or ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_citation(self, identifier: str, style: str = "apa") -> str:
        """Retrieves formatted citation string."""
        raise NotImplementedError
