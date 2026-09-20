import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from literax.providers.scopus import ScopusProvider
from literax.models import SearchQuery

@pytest.mark.asyncio
async def test_scopus_provider_no_key():
    provider = ScopusProvider(api_key=None)
    results = await provider.search(SearchQuery(raw_query="machine learning"))
    assert results == []

@pytest.mark.asyncio
async def test_scopus_provider_search_mock():
    mock_response_data = {
        "search-results": {
            "entry": [
                {
                    "dc:identifier": "SCOPUS_ID:85123456789",
                    "dc:title": "Deep Learning for Phishing Detection",
                    "dc:creator": "Smith, J.",
                    "prism:coverDate": "2024-05-12",
                    "prism:publicationName": "Computers & Security",
                    "prism:doi": "10.1016/j.cose.2024.103982",
                    "citedby-count": "42",
                    "openaccessFlag": "true",
                    "link": [{"@ref": "scopus", "@href": "https://www.scopus.com/inward/record.uri"}]
                }
            ]
        }
    }

    provider = ScopusProvider(api_key="test_api_key", inst_token="test_inst_token")

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response_data
        mock_get.return_value = mock_resp

        results = await provider.search(SearchQuery(raw_query="phishing", limit=5))
        assert len(results) == 1
        paper = results[0]
        assert paper.title == "Deep Learning for Phishing Detection"
        assert paper.doi == "10.1016/j.cose.2024.103982"
        assert paper.year == 2024
        assert paper.citation_count == 42
        assert paper.open_access is True
        assert paper.source == "Scopus"
        assert len(paper.authors) == 1
        assert paper.authors[0].name == "Smith, J."
