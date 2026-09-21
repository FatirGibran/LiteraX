import pytest
from literax.nlp.expander import QueryExpander

def test_query_expander_indonesian_translation():
    query = "deteksi phishing menggunakan machine learning"
    en_trans = QueryExpander.translate_to_english(query)
    assert "detection" in en_trans
    assert "using" in en_trans

def test_query_expander_generates_academic_variants():
    query = "deteksi phishing menggunakan machine learning"
    variants = QueryExpander.expand(query)

    assert len(variants) >= 2
    assert any("phishing detection" in v for v in variants)

def test_query_expander_get_synonyms():
    synonyms = QueryExpander.get_synonyms("machine learning")
    assert "deep learning" in synonyms
    assert "ML" in synonyms

    empty = QueryExpander.get_synonyms("non_existent_topic_xyz")
    assert empty == []
