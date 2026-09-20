import pytest
from unittest.mock import patch, AsyncMock
from literax.synthesis.doi_resolver import DoiResolver

def test_doi_normalization():
    resolver = DoiResolver()
    assert resolver.normalize_doi("https://doi.org/10.1145/3372278.3390680") == "10.1145/3372278.3390680"
    assert resolver.normalize_doi("http://dx.doi.org/10.1016/j.cose.2024.103982") == "10.1016/j.cose.2024.103982"
    assert resolver.normalize_doi("doi: 10.1000/182") == "10.1000/182"
    assert resolver.normalize_doi("10.1000/182") == "10.1000/182"
