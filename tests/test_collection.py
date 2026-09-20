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

    reloaded_manager = PaperCollectionManager(persistence_file=storage_file)
    assert reloaded_manager.count(user_id) == 2
    papers = reloaded_manager.get_papers(user_id)
    assert papers[0].title == paper1.title
    assert papers[1].title == paper2.title

    md_export = reloaded_manager.export_collection(user_id, export_format="markdown")
    assert "| **Deep Learning Approaches for Security** |" in md_export
    assert "| **Fuzzy String Matching in Python** |" in md_export

    csv_export = reloaded_manager.export_collection(user_id, export_format="csv")
    assert "Deep Learning Approaches for Security" in csv_export
    assert "Fuzzy String Matching in Python" in csv_export

    bib_export = reloaded_manager.export_collection(user_id, export_format="bibtex")
    assert "@article{" in bib_export
    assert "doi={10.1016/j.sec.2024.01}" in bib_export

    assert reloaded_manager.remove_paper(user_id, "p1") is True
    assert reloaded_manager.count(user_id) == 1

    reloaded_manager.clear_collection(user_id)
    assert reloaded_manager.count(user_id) == 0
