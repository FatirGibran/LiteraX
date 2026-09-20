import pytest
from unittest.mock import patch, AsyncMock
from literax.synthesis.doi_resolver import DoiResolver

def test_doi_normalization():
    resolver = DoiResolver()
    assert resolver.normalize_doi("https://doi.org/10.1145/3372278.3390680") == "10.1145/3372278.3390680"
    assert resolver.normalize_doi("http://dx.doi.org/10.1016/j.cose.2024.103982") == "10.1016/j.cose.2024.103982"
    assert resolver.normalize_doi("doi: 10.1000/182") == "10.1000/182"
    assert resolver.normalize_doi("10.1000/182") == "10.1000/182"

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
