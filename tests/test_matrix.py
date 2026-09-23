import json
from literax.models import Paper, Author
from literax.synthesis.matrix import LiteratureMatrixBuilder

def test_literature_matrix_build_and_exports():
    p1 = Paper(
        id="p1",
        title="Transformer for NLP",
        abstract="We propose an attention mechanism with high accuracy.",
        authors=[Author(name="Vaswani et al.")],
        year=2017,
        doi="10.5555/transformer",
        source="ArXiv"
    )
    
    matrix = LiteratureMatrixBuilder.build_matrix("Attention Models", [p1])
    assert matrix.topic == "Attention Models"
    assert len(matrix.rows) == 1
    assert matrix.row_count == 1
    assert matrix.rows[0].paper_title == "Transformer for NLP"

    md = LiteratureMatrixBuilder.export(matrix, "markdown")
    assert "# 📚 Literature Review Matrix: Attention Models" in md

    csv_data = LiteratureMatrixBuilder.export(matrix, "csv")
    assert "Paper Title,Authors,Year" in csv_data
    assert "Transformer for NLP" in csv_data

    json_data = LiteratureMatrixBuilder.export(matrix, "json")
    parsed = json.loads(json_data)
    assert parsed["topic"] == "Attention Models"
    assert len(parsed["rows"]) == 1

def test_literature_matrix_supported_formats():
    assert LiteratureMatrixBuilder.is_format_supported("markdown") is True
    assert LiteratureMatrixBuilder.is_format_supported("CSV") is True
    assert LiteratureMatrixBuilder.is_format_supported("bibtex") is True
    assert LiteratureMatrixBuilder.is_format_supported("JSON") is True
    assert LiteratureMatrixBuilder.is_format_supported("pdf") is False
    assert len(LiteratureMatrixBuilder.SUPPORTED_EXPORT_FORMATS) == 4
