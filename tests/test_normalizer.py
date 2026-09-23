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

def test_extract_filters():
    # 1. Scopus prefix
    q1, f1 = QueryNormalizer.extract_filters("scopus: machine learning")
    assert q1 == "machine learning"
    assert f1.get("providers") == ["scopus"]

    # 2. Sinta prefix
    q2, f2 = QueryNormalizer.extract_filters("sinta: sistem pakar")
    assert q2 == "sinta" or q2 == "sistem pakar"
    assert q2 == "sistem pakar"
    assert f2.get("providers") == ["sinta"]

    # 3. Open Access prefix
    q3, f3 = QueryNormalizer.extract_filters("oa: deep neural networks")
    assert q3 == "deep neural networks"
    assert f3.get("open_access_only") is True

    # 4. Year prefix
    q4, f4 = QueryNormalizer.extract_filters("year:2024 quantum computing")
    assert q4 == "quantum computing"
    assert f4.get("year_start") == 2024

    # 5. Combined filters
    q5, f5 = QueryNormalizer.extract_filters("scopus: year:2025 cyber security")
    assert q5 == "cyber security"
    assert f5.get("providers") == ["scopus"]
    assert f5.get("year_start") == 2025

    # 6. No filters
    q6, f6 = QueryNormalizer.extract_filters("transformer attention")
    assert q6 == "transformer attention"
    assert f6 == {}

    # 7. Priority prefixes
    q7, f7 = QueryNormalizer.extract_filters("scopus dulu: federated learning")
    assert q7 == "federated learning"
    assert f7.get("priority") == "scopus"

    q8, f8 = QueryNormalizer.extract_filters("sinta first: deteksi kecurangan")
    assert q8 == "deteksi kecurangan"
    assert f8.get("priority") == "sinta"

    q9, f9 = QueryNormalizer.extract_filters("priority:openalex knowledge graph")
    assert q9 == "knowledge graph"
    assert f9.get("priority") == "openalex"

