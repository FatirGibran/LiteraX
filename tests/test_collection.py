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

    # Test get_paper_by_id and filter_by_year
    found = reloaded_manager.get_paper_by_id(user_id, "p2")
    assert found is not None
    assert found.title == paper2.title

    not_found = reloaded_manager.get_paper_by_id(user_id, "non_existent_id")
    assert not_found is None

    papers_2023 = reloaded_manager.filter_by_year(user_id, 2023)
    assert len(papers_2023) == 1
    assert papers_2023[0].id == "p2"

    papers_2020 = reloaded_manager.filter_by_year(user_id, 2020)
    assert len(papers_2020) == 0

    assert reloaded_manager.remove_paper(user_id, "p1") is True
    assert reloaded_manager.count(user_id) == 1

    reloaded_manager.clear_collection(user_id)
    assert reloaded_manager.count(user_id) == 0


def test_collection_has_paper(tmp_path):
    manager = PaperCollectionManager(persistence_file=tmp_path / "coll.json")
    user = "alice"
    paper = Paper(id="p_has", title="Testing has_paper", doi="10.1234/test.doi", source="ArXiv")

    assert manager.has_paper(user, "p_has") is False
    assert manager.has_paper(user, "10.1234/test.doi") is False

    manager.add_paper(user, paper)
    assert manager.has_paper(user, "p_has") is True
    assert manager.has_paper(user, "10.1234/test.doi") is True
    assert manager.has_paper(user, "p_other") is False

def test_collection_supported_export_formats():
    assert "markdown" in PaperCollectionManager.SUPPORTED_EXPORT_FORMATS
    assert "csv" in PaperCollectionManager.SUPPORTED_EXPORT_FORMATS
    assert "bibtex" in PaperCollectionManager.SUPPORTED_EXPORT_FORMATS
    assert PaperCollectionManager.is_format_supported("markdown") is True
    assert PaperCollectionManager.is_format_supported("CSV") is True
    assert PaperCollectionManager.is_format_supported("bibtex") is True
    assert PaperCollectionManager.is_format_supported("pdf") is False

def test_collection_filter_source_and_open_access():
    manager = PaperCollectionManager()
    user = "bob"
    p1 = Paper(id="p1", title="Paper 1", source="Scopus", open_access=True)
    p2 = Paper(id="p2", title="Paper 2", source="Crossref", open_access=False)
    p3 = Paper(id="p3", title="Paper 3", source="Scopus / ScienceDirect", open_access=False)

    manager.add_paper(user, p1)
    manager.add_paper(user, p2)
    manager.add_paper(user, p3)

    scopus_papers = manager.filter_by_source(user, "scopus")
    assert len(scopus_papers) == 2
    assert {p.id for p in scopus_papers} == {"p1", "p3"}

    crossref_papers = manager.filter_by_source(user, "crossref")
    assert len(crossref_papers) == 1
    assert crossref_papers[0].id == "p2"

    oa_papers = manager.filter_open_access(user)
    assert len(oa_papers) == 1
    assert oa_papers[0].id == "p1"

def test_collection_get_all_users_and_total_papers():
    manager = PaperCollectionManager()
    assert manager.get_all_users() == []
    assert manager.total_papers_stored == 0

    p1 = Paper(id="p1", title="Title 1", source="Source 1")
    p2 = Paper(id="p2", title="Title 2", source="Source 2")

    manager.add_paper("user_a", p1)
    manager.add_paper("user_b", p2)

    users = manager.get_all_users()
    assert len(users) == 2
    assert "user_a" in users
    assert "user_b" in users
    assert manager.total_papers_stored == 2

