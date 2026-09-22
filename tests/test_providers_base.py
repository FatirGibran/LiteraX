from typing import List, Optional
from literax.providers.base import ResearchProvider
from literax.models import Paper, SearchQuery

class DummyProvider(ResearchProvider):
    name = "Dummy"
    requires_auth = False

    async def search(self, query: SearchQuery) -> List[Paper]:
        return []

    async def get_paper(self, identifier: str) -> Optional[Paper]:
        return None

    async def get_citation(self, identifier: str, style: str = "apa") -> str:
        return ""

class DummyAuthRequiredProvider(ResearchProvider):
    name = "DummyAuth"
    requires_auth = True

    async def search(self, query: SearchQuery) -> List[Paper]:
        return []

    async def get_paper(self, identifier: str) -> Optional[Paper]:
        return None

    async def get_citation(self, identifier: str, style: str = "apa") -> str:
        return ""

def test_research_provider_defaults():
    provider = DummyProvider()
    assert provider.name == "Dummy"
    assert provider.timeout == 10.0
    assert provider.is_authenticated is True

    auth_provider = DummyAuthRequiredProvider()
    assert auth_provider.is_authenticated is False
