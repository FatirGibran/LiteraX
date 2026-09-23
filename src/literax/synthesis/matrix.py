import csv
import io
from typing import List
from literax.models import Paper, LiteratureMatrix, LiteratureMatrixRow
from literax.synthesis.analyzer import PaperAnalyzer

class LiteratureMatrixBuilder:
    """Builds comparative Literature Review Matrices and handles Markdown/CSV exports."""

    SUPPORTED_EXPORT_FORMATS = ["markdown", "csv", "bibtex", "json"]

    @classmethod
    def is_format_supported(cls, export_format: str) -> bool:
        """Returns True if the specified export format is supported."""
        return export_format.lower().strip() in cls.SUPPORTED_EXPORT_FORMATS

    @classmethod
    def build_matrix(cls, topic: str, papers: List[Paper]) -> LiteratureMatrix:
        rows: List[LiteratureMatrixRow] = []

        for p in papers:
            analysis = PaperAnalyzer.heuristic_extract(p)
            author_str = p.authors[0].name if p.authors else "Unknown"
            if len(p.authors) > 1:
                author_str += " et al."

            rows.append(LiteratureMatrixRow(
                paper_title=p.title,
                authors=author_str,
                year=p.year,
                method=", ".join(analysis.algorithms_used[:2]),
                dataset=analysis.dataset,
                result=analysis.key_findings[:80] + ("..." if len(analysis.key_findings) > 80 else ""),
                limitation=analysis.limitations[:80] + ("..." if len(analysis.limitations) > 80 else ""),
                doi=p.doi
            ))

        return LiteratureMatrix(topic=topic, rows=rows)

    @classmethod
    def to_markdown(cls, matrix: LiteratureMatrix) -> str:
        lines = [
            f"# 📚 Literature Review Matrix: {matrix.topic}\n",
            "| Paper | Authors | Year | Method | Dataset | Key Result | Limitation |",
            "| :--- | :--- | :---: | :--- | :--- | :--- | :--- |"
        ]
        for r in matrix.rows:
            lines.append(
                f"| **{r.paper_title}** | {r.authors} | {r.year or 'N/A'} | {r.method} | {r.dataset} | {r.result} | {r.limitation} |"
            )
        return "\n".join(lines)

    @classmethod
    def to_csv(cls, matrix: LiteratureMatrix) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Paper Title", "Authors", "Year", "Method", "Dataset", "Key Result", "Limitation", "DOI"])
        for r in matrix.rows:
            writer.writerow([r.paper_title, r.authors, r.year, r.method, r.dataset, r.result, r.limitation, r.doi])
        return output.getvalue()

    @classmethod
    def to_bibtex(cls, matrix: LiteratureMatrix) -> str:
        """Exports all matrix rows as formatted BibTeX citation entries."""
        import re
        entries = []
        for idx, r in enumerate(matrix.rows, 1):
            first_author = re.sub(r"\W", "", r.authors.split()[0].lower()) if r.authors else "anon"
            year = str(r.year or "nodate")
            first_word = re.sub(r"\W", "", r.paper_title.split()[0].lower()) if r.paper_title else "work"
            cite_key = f"{first_author}{year}{first_word}_{idx}"
            doi_str = f"  doi={{{r.doi}}},\n" if r.doi else ""
            year_str = f"  year={{{r.year}}},\n" if r.year else ""
            entries.append(
                f"@article{{{cite_key},\n"
                f"  title={{{r.paper_title}}},\n"
                f"  author={{{r.authors}}},\n"
                f"  note={{Method: {r.method}, Dataset: {r.dataset}}},\n"
                f"{year_str}"
                f"{doi_str}"
                f"}}"
            )
        return "\n\n".join(entries)

    @classmethod
    def to_json(cls, matrix: LiteratureMatrix, indent: int = 2) -> str:
        """Exports the literature matrix as a formatted JSON string."""
        import json
        return json.dumps(matrix.model_dump(), indent=indent)

    @classmethod
    def export(cls, matrix: LiteratureMatrix, export_format: str = "markdown") -> str:
        fmt = export_format.lower().strip()
        if fmt == "csv":
            return cls.to_csv(matrix)
        elif fmt == "bibtex":
            return cls.to_bibtex(matrix)
        elif fmt == "json":
            return cls.to_json(matrix)
        else:
            return cls.to_markdown(matrix)
