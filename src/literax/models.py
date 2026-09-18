from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Author(BaseModel):
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None

class Paper(BaseModel):
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

class SearchQuery(BaseModel):
    raw_query: str
    expanded_queries: List[str] = Field(default_factory=list)
    providers: Optional[List[str]] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    limit: int = 10
    open_access_only: bool = False

class TokenCorrection(BaseModel):
    original: str
    corrected: str
    status: str = "UNCHANGED"  # UNCHANGED, CORRECTED, PROTECTED
    confidence: float = 1.0
    distance_metric: Optional[str] = None

class CorrectionResult(BaseModel):
    original_query: str
    corrected_query: str
    overall_confidence: float
    action: str  # AUTO_CORRECTED, PROMPT_USER, UNCHANGED
    tokens: List[TokenCorrection] = Field(default_factory=list)
    tokens_changed: List[Dict[str, Any]] = Field(default_factory=list)

class PaperAnalysis(BaseModel):
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
    paper_title: str
    authors: str
    year: Optional[int] = None
    method: str
    dataset: str
    result: str
    limitation: str
    doi: Optional[str] = None

class LiteratureMatrix(BaseModel):
    topic: str
    rows: List[LiteratureMatrixRow] = Field(default_factory=list)

class ResearchGapItem(BaseModel):
    title: str
    description: str
    category: str  # Methodology, Dataset, Scalability, Evaluation
    supporting_papers: List[str] = Field(default_factory=list)

class ResearchGapReport(BaseModel):
    topic: str
    gaps: List[ResearchGapItem] = Field(default_factory=list)

class CitationResponse(BaseModel):
    paper_id: str
    style: str
    citation: str
