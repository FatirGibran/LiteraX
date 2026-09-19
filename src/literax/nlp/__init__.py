"""NLP & Query Processing Package for LiteraX."""

from literax.nlp.normalizer import QueryNormalizer
from literax.nlp.protected_terms import ProtectedTermsManager
from literax.nlp.fuzzy import FuzzyAutoCorrect
from literax.nlp.expander import QueryExpander

__all__ = [
    "QueryNormalizer",
    "ProtectedTermsManager",
    "FuzzyAutoCorrect",
    "QueryExpander",
]
