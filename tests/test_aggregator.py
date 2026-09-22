import pytest
from literax.engine.aggregator import PaperAggregator
from literax.providers.base import ResearchProvider
from literax.models import Paper, SearchQuery

class MockTestProvider(ResearchProvider):
    name = "MockTest"
    requires_auth = False

    async def search(self, query: SearchQuery):
        return [
            Paper(
                id="mock_1",
                title="Mock Paper in AI",
                source="MockTest",
                citation_count=5
            )
        ]

    async def get_paper(self, identifier: str):
        return None

    async def get_citation(self, identifier: str, style: str = "apa"):
        return ""

def test_aggregator_providers_and_registration():
    aggregator = PaperAggregator(providers=[])
    assert aggregator.provider_names == []

    mock_prov = MockTestProvider()
    aggregator.register_provider(mock_prov)
    assert aggregator.provider_names == ["MockTest"]

@pytest.mark.asyncio
async def test_aggregator_search_with_mock():
    mock_prov = MockTestProvider()
    aggregator = PaperAggregator(providers=[mock_prov])
    results = await aggregator.search(SearchQuery(raw_query="mock paper", limit=5))
    assert len(results) == 1
    assert results[0].title == "Mock Paper in AI"
