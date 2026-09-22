from literax.providers.crossref import CrossrefProvider

def test_crossref_clean_query_string():
    raw = "   machine   learning   phishing   \n\t"
    cleaned = CrossrefProvider.clean_query_string(raw)
    assert cleaned == "machine learning phishing"

def test_crossref_provider_initialization():
    provider = CrossrefProvider(mailto="test@test.com")
    assert provider.mailto == "test@test.com"
    assert provider.name == "Crossref"
    assert provider.requires_auth is False
