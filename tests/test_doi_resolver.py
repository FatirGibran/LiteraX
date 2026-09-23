import pytest
from unittest.mock import patch, AsyncMock
from literax.synthesis.doi_resolver import DoiResolver

def test_doi_normalization():
    resolver = DoiResolver()
    assert resolver.normalize_doi("https://doi.org/10.1145/3372278.3390680") == "10.1145/3372278.3390680"
    assert resolver.normalize_doi("http://dx.doi.org/10.1016/j.cose.2024.103982") == "10.1016/j.cose.2024.103982"
    assert resolver.normalize_doi("doi: 10.1000/182") == "10.1000/182"
    assert resolver.normalize_doi("10.1000/182") == "10.1000/182"

def test_doi_resolver_supported_styles():
    resolver = DoiResolver()
    assert len(resolver.supported_styles) >= 7
    assert "apa" in resolver.supported_styles
    assert "bibtex" in resolver.supported_styles
    assert "ris" in resolver.supported_styles

def test_cache_hits_and_misses():
    resolver = DoiResolver(ttl_seconds=60)
    doi = "10.1145/12345"
    style = "apa"

    assert resolver.get_cached(doi, style) is None
    assert resolver.misses == 1
    assert resolver.hits == 0

    resolver.set_cache(doi, style, "Sample APA Citation")
    assert resolver.cache_size == 1

    cached = resolver.get_cached(doi, style)
    assert cached == "Sample APA Citation"
    assert resolver.hits == 1

    resolver.clear_cache()
    assert resolver.cache_size == 0
    assert resolver.hits == 0

def test_cache_hit_rate_and_is_cached():
    resolver = DoiResolver(ttl_seconds=300)
    doi = "10.5555/example"
    style = "ieee"
    assert not resolver.is_cached(doi, style)
    assert resolver.cache_hit_rate == 0.0

    resolver.set_cache(doi, style, "Example IEEE Citation")
    assert resolver.is_cached(doi, style)

    resolver.get_cached(doi, style)
    assert resolver.cache_hit_rate == 1.0

@pytest.mark.asyncio
async def test_resolve_remote_mock():
    resolver = DoiResolver()
    doi = "10.1016/j.test.2024"

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = "Author, A. (2024). Test Title. Journal of Testing."
        mock_get.return_value = mock_resp

        result = await resolver.resolve(doi, style="apa")
        assert result == "Author, A. (2024). Test Title. Journal of Testing."
        assert resolver.cache_size == 1

        mock_get.reset_mock()
        cached_result = await resolver.resolve(doi, style="apa")
        assert cached_result == "Author, A. (2024). Test Title. Journal of Testing."
        mock_get.assert_not_called()
