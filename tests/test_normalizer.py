from literax.nlp.normalizer import QueryNormalizer

def test_query_normalizer_empty():
    assert QueryNormalizer.normalize("") == ""
    assert QueryNormalizer.normalize("   ") == ""
    assert QueryNormalizer.tokenize("") == []

def test_query_normalizer_preserves_hyphenated_terms():
    text = "deep-learning and f1-score in covid-19"
    norm = QueryNormalizer.normalize(text)
    assert "deep-learning" in norm
    assert "f1-score" in norm
    assert "covid-19" in norm

def test_query_normalizer_quotes_and_punctuation():
    text = 'search for "transformer models": with accuracy, precision.'
    norm = QueryNormalizer.normalize(text)
    assert '"transformer models"' in norm
    tokens = QueryNormalizer.tokenize(norm)
    assert "accuracy" in tokens
    assert "precision" in tokens
    assert ":" not in tokens

def test_clean_whitespace():
    assert QueryNormalizer.clean_whitespace("  hello   world  \t\n") == "hello world"
