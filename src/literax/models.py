from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Author(BaseModel):
    """Represents a paper author with optional institutional affiliation and ORCID."""
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None

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
    def primary_author(self) -> str:
        """Returns the name of the first author or 'Anonymous' if empty."""
        return self.authors[0].name if self.authors else "Anonymous"

class SearchQuery(BaseModel):
    """Academic search query request payload with filter parameters."""
    raw_query: str
    expanded_queries: List[str] = Field(default_factory=list)
    providers: Optional[List[str]] = None
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

class ResearchGapItem(BaseModel):
    """Identified research gap or unexplored intersection in current literature."""
    title: str
    description: str
    category: str  # Methodology, Dataset, Scalability, Evaluation
    supporting_papers: List[str] = Field(default_factory=list)

class ResearchGapReport(BaseModel):
    """Comprehensive synthesis report highlighting identified research gaps."""
    topic: str
    gaps: List[ResearchGapItem] = Field(default_factory=list)

class CitationResponse(BaseModel):
    """Formatted academic citation response across various reference styles."""
    paper_id: str
    style: str
    citation: str
