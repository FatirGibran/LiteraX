import pytest
from literax.models import Paper, Author
from literax.storage.collection import PaperCollectionManager

def test_collection_crud_and_exports(tmp_path):
    storage_file = tmp_path / "test_collections.json"
    manager = PaperCollectionManager(persistence_file=storage_file)

    user_id = "user_123"
    paper1 = Paper(
        id="p1",
        title="Deep Learning Approaches for Security",
        doi="10.1016/j.sec.2024.01",
        year=2024,
        authors=[Author(name="John Doe"), Author(name="Jane Smith")],
        journal="Journal of Cyber",
        citation_count=15,
        source="Crossref"
    )
    paper2 = Paper(
        id="p2",
        title="Fuzzy String Matching in Python",
        doi="10.1145/fuzzy.2023",
        year=2023,
        authors=[Author(name="Alice Brown")],
        journal="ACM Computing",
        citation_count=8,
        source="OpenAlex"
    )

    assert manager.count(user_id) == 0
    assert manager.get_papers(user_id) == []

    assert manager.add_paper(user_id, paper1) is True
    assert manager.count(user_id) == 1

    assert manager.add_paper(user_id, paper1) is False
    assert manager.count(user_id) == 1

    assert manager.add_paper(user_id, paper2) is True
    assert manager.count(user_id) == 2
