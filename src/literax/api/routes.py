from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from literax.models import (
    CorrectionResult,
    Paper,
    SearchQuery,
    PaperAnalysis,
    LiteratureMatrix,
    ResearchGapReport,
    CitationResponse
)
from literax.nlp.fuzzy import FuzzyAutoCorrect
from literax.engine.aggregator import PaperAggregator
from literax.synthesis.citation import CitationGenerator
from literax.synthesis.analyzer import PaperAnalyzer
from literax.synthesis.matrix import LiteratureMatrixBuilder
from literax.synthesis.gap_finder import ResearchGapFinder

router = APIRouter(prefix="/api/v1")
fuzzy_engine = FuzzyAutoCorrect()
aggregator = PaperAggregator()

class CorrectRequest(BaseModel):
    query: str

class MatrixRequest(BaseModel):
    topic: str
    papers: List[Paper]

class MatrixExportRequest(BaseModel):
    matrix: LiteratureMatrix
    format: str = "markdown"

class GapRequest(BaseModel):
    topic: str
    papers: List[Paper]

@router.post("/correct", response_model=CorrectionResult)
async def correct_query(req: CorrectRequest):
    """Corrects user query typos and computes fuzzy logic confidence score."""
    return fuzzy_engine.process_query(req.query)

@router.post("/search", response_model=List[Paper])
async def search_literature(query: SearchQuery):
    """Searches across academic providers, deduplicates, and ranks by relevance."""
    # Process auto-correct if needed
    correction = fuzzy_engine.process_query(query.raw_query)
    effective_query = query.model_copy()
    if correction.action == "AUTO_CORRECTED":
        effective_query.raw_query = correction.corrected_query

    return await aggregator.search(effective_query)

@router.post("/analyze", response_model=PaperAnalysis)
async def analyze_paper(paper: Paper):
    """Extracts structured research taxonomy from paper metadata and abstract."""
    return await PaperAnalyzer.analyze(paper)

@router.post("/matrix", response_model=LiteratureMatrix)
async def generate_matrix(req: MatrixRequest):
    """Generates a structured comparative literature review matrix."""
    return LiteratureMatrixBuilder.build_matrix(req.topic, req.papers)

@router.post("/matrix/export")
async def export_matrix(req: MatrixExportRequest):
    """Exports a literature matrix into Markdown, CSV, or BibTeX."""
    content = LiteratureMatrixBuilder.export(req.matrix, req.format)
    return {"format": req.format, "content": content}

@router.post("/gap", response_model=ResearchGapReport)
async def find_research_gaps(req: GapRequest):
    """Identifies potential research gaps across a cluster of papers."""
    return ResearchGapFinder.find_gaps(req.topic, req.papers)

@router.get("/papers/{id}/citation", response_model=CitationResponse)
async def get_citation(
    id: str,
    title: str = Query("Untitled"),
    year: Optional[int] = Query(None),
    journal: Optional[str] = Query(None),
    doi: Optional[str] = Query(None),
    style: str = Query("apa")
):
    """Generates a citation in APA, IEEE, Harvard, Vancouver, or BibTeX."""
    paper = Paper(
        id=id,
        title=title,
        year=year,
        journal=journal,
        doi=doi,
        source="Crossref"
    )
    cit_text = CitationGenerator.generate(paper, style=style)
    return CitationResponse(paper_id=id, style=style, citation=cit_text)
