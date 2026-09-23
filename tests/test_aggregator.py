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

class MockMultiSourceProvider(ResearchProvider):
    def __init__(self, name: str, papers: list[Paper]):
        self.name = name
        self._papers = papers
        self.requires_auth = False

    async def search(self, query: SearchQuery):
        return self._papers

    async def get_paper(self, identifier: str):
        return None

    async def get_citation(self, identifier: str, style: str = "apa"):
        return ""

@pytest.mark.asyncio
async def test_aggregator_filtering_by_provider_and_criteria():
    scopus_paper = Paper(
        id="scopus_1",
        title="Scopus Deep Learning Research",
        source="Scopus",
        year=2024,
        open_access=False
    )
    sinta_paper = Paper(
        id="sinta_1",
        title="SINTA Jurnal Nasional Informatika",
        source="GARUDA / SINTA",
        year=2022,
        open_access=True,
        full_text_url="https://garuda.kemdikbud.go.id/article.pdf"
    )

    prov_scopus = MockMultiSourceProvider("Scopus", [scopus_paper])
    prov_sinta = MockMultiSourceProvider("GARUDA / SINTA", [sinta_paper])

    aggregator = PaperAggregator(providers=[prov_scopus, prov_sinta])

    # 1. Search all
    all_res = await aggregator.search(SearchQuery(raw_query="learning"))
    assert len(all_res) == 2

    # 2. Filter Scopus only
    scopus_res = await aggregator.search(SearchQuery(raw_query="learning", providers=["scopus"]))
    assert len(scopus_res) == 1
    assert scopus_res[0].source == "Scopus"

    # 3. Filter SINTA only
    sinta_res = await aggregator.search(SearchQuery(raw_query="learning", providers=["sinta"]))
    assert len(sinta_res) == 1
    assert sinta_res[0].source == "GARUDA / SINTA"

    # 4. Filter Open Access only
    oa_res = await aggregator.search(SearchQuery(raw_query="learning", open_access_only=True))
    assert len(oa_res) == 1
    assert oa_res[0].id == "sinta_1"

    # 5. Filter Year >= 2023
    year_res = await aggregator.search(SearchQuery(raw_query="learning", year_start=2023))
    assert len(year_res) == 1
    assert year_res[0].year == 2024
