import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from literax.providers.scopus import ScopusProvider
from literax.models import SearchQuery

@pytest.mark.asyncio
async def test_scopus_provider_no_key():
    provider = ScopusProvider(api_key=None)
    results = await provider.search(SearchQuery(raw_query="machine learning"))
    assert results == []
