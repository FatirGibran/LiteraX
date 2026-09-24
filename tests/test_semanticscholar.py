import pytest
from unittest.mock import patch, MagicMock
from literax.providers.semanticscholar import SemanticScholarProvider
from literax.models import SearchQuery

@pytest.mark.asyncio
async def test_semanticscholar_search_success():
    provider = SemanticScholarProvider()
    mock_data = {
        "data": [
            {
                "paperId": "s2_12345",
                "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                "abstract": "We introduce a new language representation model called BERT.",
                "year": 2019,
                "authors": [{"name": "Jacob Devlin"}, {"name": "Ming-Wei Chang"}],
                "venue": "NAACL-HLT",
                "citationCount": 50000,
                "isOpenAccess": True,
                "openAccessPdf": {"url": "https://arxiv.org/pdf/1810.04805.pdf"},
                "externalIds": {"DOI": "10.18653/v1/N19-1423"}
            }
        ]
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_data
        mock_get.return_value = mock_resp

        results = await provider.search(SearchQuery(raw_query="bert", limit=5))
        assert len(results) == 1
        paper = results[0]
        assert paper.id == "s2_12345"
        assert paper.title == "BERT: Pre-training of Deep Bidirectional Transformers"
        assert paper.abstract == "We introduce a new language representation model called BERT."
        assert paper.year == 2019
        assert len(paper.authors) == 2
        assert paper.authors[0].name == "Jacob Devlin"
        assert paper.journal == "NAACL-HLT"
        assert paper.citation_count == 50000
        assert paper.open_access is True
        assert paper.doi == "10.18653/v1/N19-1423"
        assert paper.full_text_url == "https://arxiv.org/pdf/1810.04805.pdf"
        assert paper.landing_page_url == "https://www.semanticscholar.org/paper/s2_12345"

@pytest.mark.asyncio
async def test_semanticscholar_with_api_key():
    provider = SemanticScholarProvider(api_key="secret_s2_key")
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": []}
        mock_get.return_value = mock_resp

        results = await provider.search(SearchQuery(raw_query="transformer"))
        assert results == []
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["headers"].get("x-api-key") == "secret_s2_key"

@pytest.mark.asyncio
async def test_semanticscholar_non_200_status():
    provider = SemanticScholarProvider()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_get.return_value = mock_resp

        results = await provider.search(SearchQuery(raw_query="nlp"))
        assert results == []

@pytest.mark.asyncio
async def test_semanticscholar_exception_handling():
    provider = SemanticScholarProvider()
    with patch("httpx.AsyncClient.get", side_effect=Exception("Network failure")):
        results = await provider.search(SearchQuery(raw_query="graph neural network"))
        assert results == []

@pytest.mark.asyncio
async def test_semanticscholar_default_stubs():
    provider = SemanticScholarProvider()
    assert await provider.get_paper("dummy_id") is None
    assert await provider.get_citation("dummy_id") == ""
