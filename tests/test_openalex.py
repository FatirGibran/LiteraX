from literax.providers.openalex import OpenAlexProvider

def test_decode_abstract_valid():
    inverted_index = {
        "Deep": [0],
        "learning": [1],
        "for": [2],
        "security": [3]
    }
    result = OpenAlexProvider.decode_abstract(inverted_index)
    assert result == "Deep learning for security"

def test_decode_abstract_edge_cases():
    assert OpenAlexProvider.decode_abstract(None) is None
    assert OpenAlexProvider.decode_abstract({}) is None
    assert OpenAlexProvider.decode_abstract({"word": []}) is None
    assert OpenAlexProvider.decode_abstract("not a dict") is None  # type: ignore
