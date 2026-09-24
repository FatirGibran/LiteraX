from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Author(BaseModel):
    """Represents a paper author with optional institutional affiliation and ORCID."""
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None

    @property
    def display_name(self) -> str:
        """Returns author name stripped of whitespace."""
        return self.name.strip()

    @property
    def has_affiliation(self) -> bool:
        """Returns True if the author has non-empty affiliation."""
        return bool(self.affiliation and self.affiliation.strip())

class Paper(BaseModel):
    """Core academic paper metadata model unified across all providers."""
    id: str
    title: str
    abstract: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    authors: List[Author] = Field(default_factory=list)
    journal: Optional[str] = None
    citation_count: int = 0
    source: str
    open_access: bool = False
    full_text_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    composite_relevance: float = 0.0

    @property
    def has_doi(self) -> bool:
        """Returns True if the paper has a non-empty DOI."""
        return bool(self.doi and self.doi.strip())

    @property
    def has_full_text(self) -> bool:
        """Returns True if full text URL is available and non-empty."""
        return bool(self.full_text_url and self.full_text_url.strip())

    @property
    def has_abstract(self) -> bool:
        """Returns True if abstract is available and non-empty."""
        return bool(self.abstract and self.abstract.strip())

    @property
    def primary_author(self) -> str:
        """Returns the name of the first author or 'Anonymous' if empty."""
        return self.authors[0].name if self.authors else "Anonymous"

    @property
    def is_recent(self) -> bool:
        """Returns True if the paper was published within the last 3 years (>= 2023)."""
        return bool(self.year and self.year >= 2023)

    @property
    def display_title(self) -> str:
        """Returns cleaned title without surrounding whitespace."""
        return self.title.strip()

    @property
    def is_highly_cited(self) -> bool:
        """Returns True if citation_count is 100 or greater."""
        return self.citation_count >= 100

    @property
    def authors_summary(self) -> str:
        """Returns short author summary (e.g. 'Doe et al.' or 'Doe & Smith' or 'Doe' or 'Anonymous')."""
        if not self.authors:
            return "Anonymous"
        names = [a.name.strip().split()[-1] if a.name.strip() else "Unknown" for a in self.authors]
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} & {names[1]}"
        return f"{names[0]} et al."

    @property
    def year_str(self) -> str:
        """Returns publication year formatted as string or 'n.d.' if unknown."""
        return str(self.year) if self.year else "n.d."

    @property
    def direct_url(self) -> Optional[str]:
        """Returns the most direct URL to access the paper (full text PDF, DOI, or landing page)."""
        if self.full_text_url and self.full_text_url.strip():
            return self.full_text_url.strip()
        if self.doi and self.doi.strip():
            clean_doi = self.doi.strip().replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
            return f"https://doi.org/{clean_doi}"
        if self.landing_page_url and self.landing_page_url.strip():
            return self.landing_page_url.strip()
        return None

    @property
    def doi_url(self) -> Optional[str]:
        """Returns normalized https://doi.org/... link if DOI is present."""
        if not self.doi or not self.doi.strip():
            return None
        clean_doi = self.doi.strip().replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        return f"https://doi.org/{clean_doi}"

    @property
    def relevance_reasoning(self) -> str:
        """Generates clear scientific reasoning explaining why this paper is recommended."""
        reasons = []
        if self.composite_relevance >= 0.85:
            reasons.append("Sangat cocok secara semantik dan terminologi dengan topik yang dicari")
        elif self.composite_relevance >= 0.65:
            reasons.append("Memiliki kecocokan konseptual dan kata kunci yang kuat")
        else:
            reasons.append("Terkait dengan konteks penelitian yang relevan")

        if self.is_highly_cited:
            reasons.append(f"artikel rujukan utama (high-impact) dengan {self.citation_count} sitasi")
        elif self.citation_count > 10:
            reasons.append(f"sudah dirujuk oleh {self.citation_count} publikasi lain")

        if self.is_recent:
            reasons.append(f"publikasi mutakhir ({self.year}) yang menyajikan State-of-the-Art (SOTA)")
        elif self.year:
            reasons.append(f"terbit pada tahun {self.year}")

        if "scopus" in self.source.lower() or "sinta 1" in self.source.lower():
            reasons.append("terindeks di jurnal/prosiding internasional bereputasi")

        return "; ".join(reasons) + "."

    def to_summary_dict(self) -> Dict[str, Any]:
        """Returns a concise summary dictionary suitable for lightweight serialization and UI previews."""
        return {
            "id": self.id,
            "title": self.display_title,
            "authors": self.authors_summary,
            "year": self.year,
            "journal": self.journal,
            "citations": self.citation_count,
            "source": self.source,
            "doi": self.doi,
            "direct_url": self.direct_url,
            "open_access": self.open_access
        }

class SearchQuery(BaseModel):
    """Academic search query request payload with filter parameters."""
    raw_query: str
    expanded_queries: List[str] = Field(default_factory=list)
    providers: Optional[List[str]] = None
    priority: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    limit: int = 10
    open_access_only: bool = False

class TokenCorrection(BaseModel):
    """Detailed result for an individual token evaluated in the spell check pipeline."""
    original: str
    corrected: str
    status: str = "UNCHANGED"  # UNCHANGED, CORRECTED, PROTECTED
    confidence: float = 1.0
    distance_metric: Optional[str] = None

    @property
    def is_corrected(self) -> bool:
        """Returns True if the token was corrected."""
        return self.status == "CORRECTED"

    @property
    def is_protected(self) -> bool:
        """Returns True if the token was recognized as a protected domain term."""
        return self.status == "PROTECTED"

class CorrectionResult(BaseModel):
    """Overall result of the fuzzy auto-correction pipeline for a search query."""
    original_query: str
    corrected_query: str
    overall_confidence: float
    action: str  # AUTO_CORRECTED, PROMPT_USER, UNCHANGED
    tokens: List[TokenCorrection] = Field(default_factory=list)
    tokens_changed: List[Dict[str, Any]] = Field(default_factory=list)

class PaperAnalysis(BaseModel):
    """Structured taxonomy decomposed from an academic paper abstract."""
    paper_id: Optional[str] = None
    title: str
    problem_statement: str
    research_objective: str
    methodology: str
    dataset: str
    algorithms_used: List[str] = Field(default_factory=list)
    evaluation_metrics: List[str] = Field(default_factory=list)
    key_findings: str
    limitations: str
    future_work: Optional[str] = None
    reasoning: Optional[str] = None

class LiteratureMatrixRow(BaseModel):
    """Row representing comparative literature synthesis for a single paper."""
    paper_title: str
    authors: str
    year: Optional[int] = None
    method: str
    dataset: str
    result: str
    limitation: str
    doi: Optional[str] = None

class LiteratureMatrix(BaseModel):
    """Complete structured literature review matrix collection."""
    topic: str
    rows: List[LiteratureMatrixRow] = Field(default_factory=list)

    @property
    def row_count(self) -> int:
        """Returns the number of rows in the matrix."""
        return len(self.rows)

class ResearchGapItem(BaseModel):
    """Identified research gap or unexplored intersection in current literature."""
    title: str
    description: str
    category: str  # Methodology, Dataset, Scalability, Evaluation
    severity: str = "Medium"  # High, Medium, Low
    supporting_papers: List[str] = Field(default_factory=list)
    novelty_opportunity: Optional[str] = None

    @property
    def is_high_severity(self) -> bool:
        """Returns True if severity is High."""
        return self.severity.lower() == "high"

    @property
    def supporting_count(self) -> int:
        """Returns the number of supporting papers associated with this research gap."""
        return len(self.supporting_papers)

class ResearchGapReport(BaseModel):
    """Comprehensive synthesis report highlighting identified research gaps."""
    topic: str
    gaps: List[ResearchGapItem] = Field(default_factory=list)

    @property
    def total_gaps(self) -> int:
        """Returns the total number of identified research gaps."""
        return len(self.gaps)

class BrainstormIdea(BaseModel):
    """Specific formulated research proposal or thesis idea."""
    title_id: str
    title_en: str
    focus: str
    suggested_methods: List[str] = Field(default_factory=list)
    suggested_datasets: List[str] = Field(default_factory=list)
    novelty_points: str
    expected_contribution: str

class BrainstormResult(BaseModel):
    """Comprehensive research brainstorming output."""
    topic: str
    core_problem: str
    ideas: List[BrainstormIdea] = Field(default_factory=list)
    methodology_landscape: str
    benchmark_datasets: List[str] = Field(default_factory=list)
    practical_challenges: List[str] = Field(default_factory=list)
    seed_papers: List[Paper] = Field(default_factory=list)

    @property
    def total_ideas(self) -> int:
        return len(self.ideas)

class CitationResponse(BaseModel):
    """Formatted academic citation response across various reference styles."""
    paper_id: str
    style: str
    citation: str
