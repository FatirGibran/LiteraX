import re
from typing import Optional
from literax.models import Paper

class CitationGenerator:
    """Generates citations across academic styles and reference formats."""

    @classmethod
    def format_authors_apa(cls, paper: Paper) -> str:
        if not paper.authors:
            return "Anonymous"
        names = []
        for a in paper.authors:
            parts = a.name.strip().split()
            if len(parts) > 1:
                last = parts[-1]
                initials = "".join([f"{p[0]}." for p in parts[:-1]])
                names.append(f"{last}, {initials}")
            else:
                names.append(a.name)
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} & {names[1]}"
        else:
            return f"{', '.join(names[:-1])}, & {names[-1]}"

    @classmethod
    def format_authors_ieee(cls, paper: Paper) -> str:
        if not paper.authors:
            return "Anonymous"
        names = []
        for a in paper.authors:
            parts = a.name.strip().split()
            if len(parts) > 1:
                initials = " ".join([f"{p[0]}." for p in parts[:-1]])
                names.append(f"{initials} {parts[-1]}")
            else:
                names.append(a.name)
        if len(names) <= 2:
            return " and ".join(names)
        return f"{names[0]} et al."

    @classmethod
    def to_apa(cls, paper: Paper) -> str:
        authors = cls.format_authors_apa(paper)
        year = f"({paper.year})" if paper.year else "(n.d.)"
        title = paper.title.rstrip(".") + "."
        journal = f"*{paper.journal}*." if paper.journal else ""
        doi = f" https://doi.org/{paper.doi}" if paper.doi else ""
        return f"{authors} {year}. {title} {journal}{doi}".strip()

    @classmethod
    def to_ieee(cls, paper: Paper) -> str:
        authors = cls.format_authors_ieee(paper)
        title = f'"{paper.title.rstrip(".")},"'
        journal = f" *{paper.journal}*," if paper.journal else ""
        year = f" {paper.year}." if paper.year else ""
        doi = f" doi: {paper.doi}." if paper.doi else ""
        return f"{authors}, {title}{journal}{year}{doi}".strip()

    @classmethod
    def to_harvard(cls, paper: Paper) -> str:
        authors = cls.format_authors_apa(paper).replace("&", "and")
        year = f"{paper.year}." if paper.year else "n.d."
        title = f"'{paper.title.rstrip('.')}',"
        journal = f" *{paper.journal}*." if paper.journal else ""
        return f"{authors} {year} {title}{journal}".strip()

    @classmethod
    def to_bibtex(cls, paper: Paper) -> str:
        # Generate bibtex citation key
        first_author = paper.authors[0].name.split()[-1].lower() if paper.authors else "anon"
        first_author = re.sub(r"\W", "", first_author)
        year = str(paper.year or "nodate")
        first_word = re.sub(r"\W", "", paper.title.split()[0].lower()) if paper.title else "work"
        cite_key = f"{first_author}{year}{first_word}"

        author_str = " and ".join([a.name for a in paper.authors]) if paper.authors else "Anonymous"
        journal_str = f"  journal={{{paper.journal}}},\n" if paper.journal else ""
        doi_str = f"  doi={{{paper.doi}}},\n" if paper.doi else ""
        year_str = f"  year={{{paper.year}}},\n" if paper.year else ""

        return (
            f"@article{{{cite_key},\n"
            f"  title={{{paper.title}}},\n"
            f"  author={{{author_str}}},\n"
            f"{journal_str}"
            f"{year_str}"
            f"{doi_str}"
            f"  publisher={{{paper.source}}}\n"
            f"}}"
        )

    @classmethod
    def to_ris(cls, paper: Paper) -> str:
        lines = ["TY  - JOUR", f"TI  - {paper.title}"]
        for a in paper.authors:
            lines.append(f"AU  - {a.name}")
        if paper.journal:
            lines.append(f"JO  - {paper.journal}")
        if paper.year:
            lines.append(f"PY  - {paper.year}")
        if paper.doi:
            lines.append(f"DO  - {paper.doi}")
        lines.append("ER  - ")
        return "\n".join(lines)

    @classmethod
    def generate(cls, paper: Paper, style: str = "apa") -> str:
        style_clean = style.lower().strip()
        if style_clean == "apa":
            return cls.to_apa(paper)
        elif style_clean == "ieee":
            return cls.to_ieee(paper)
        elif style_clean == "harvard":
            return cls.to_harvard(paper)
        elif style_clean == "bibtex":
            return cls.to_bibtex(paper)
        elif style_clean == "ris":
            return cls.to_ris(paper)
        return cls.to_apa(paper)
