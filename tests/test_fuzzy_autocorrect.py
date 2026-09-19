import pytest
from literax.nlp.normalizer import QueryNormalizer
from literax.nlp.protected_terms import ProtectedTermsManager
from literax.nlp.fuzzy import FuzzyAutoCorrect

def test_query_normalization():
    raw = "  Machine   Lerning  UNTUK   Deteksi PHISING!  "
    norm = QueryNormalizer.normalize(raw)
    tokens = QueryNormalizer.tokenize(norm)
    assert tokens == ["Machine", "Lerning", "UNTUK", "Deteksi", "PHISING"]

def test_protected_terms():
    mgr = ProtectedTermsManager()
    assert mgr.is_protected("svm")
    assert mgr.is_protected("CNN")
    assert mgr.is_protected("bert")
    assert mgr.is_protected("iot")
    assert not mgr.is_protected("phising")

def test_user_prompt_exact_autocorrect():
    fuzzy = FuzzyAutoCorrect()
    query = "machin lerning untk deteksi phising"
    res = fuzzy.process_query(query)

    assert res.original_query == "machin lerning untk deteksi phising"
    assert res.corrected_query == "machine learning untuk deteksi phishing"
    assert res.overall_confidence >= 0.90
    assert res.action == "AUTO_CORRECTED"
    assert len(res.tokens_changed) == 4

def test_protected_term_not_modified():
    fuzzy = FuzzyAutoCorrect()
    query = "klasifikasi cnn dan svm untk deteksi phising"
    res = fuzzy.process_query(query)

    tokens = [t.corrected.lower() for t in res.tokens]
    assert "cnn" in tokens
    assert "svm" in tokens
    assert "untuk" in tokens
    assert "phishing" in tokens
