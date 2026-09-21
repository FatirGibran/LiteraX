from pathlib import Path
from literax.nlp.protected_terms import ProtectedTermsManager

def test_protected_terms_default_loader():
    mgr = ProtectedTermsManager()
    assert len(mgr.protected_terms) > 0
    assert mgr.is_protected("svm")
    assert mgr.is_protected("SVM")
    assert mgr.is_protected("bert")
    assert mgr.is_protected("rag")
    assert mgr.is_protected("lora")

def test_protected_terms_hyphenated_variations():
    mgr = ProtectedTermsManager()
    assert mgr.is_protected("covid-19")
    assert mgr.is_protected("covid19")
    assert mgr.is_protected("t-sne")

def test_unprotected_term():
    mgr = ProtectedTermsManager()
    assert not mgr.is_protected("randomwordxyz123")
    assert not mgr.is_protected("")
