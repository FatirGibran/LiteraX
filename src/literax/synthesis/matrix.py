import csv
import io
from typing import List
from literax.models import Paper, LiteratureMatrix, LiteratureMatrixRow
from literax.synthesis.analyzer import PaperAnalyzer

class LiteratureMatrixBuilder:
    """Builds comparative Literature Review Matrices and handles Markdown/CSV exports."""

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
