from fastapi import APIRouter, Query, HTTPException, Header
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from literax.config import settings

from literax.models import (
    CorrectionResult,
    Paper,
    SearchQuery,
    PaperAnalysis,
    LiteratureMatrix,
    ResearchGapReport,
    CitationResponse
)
from literax.engine.benchmark import DeduplicationBenchmarkSuite, DedupBenchmarkResult
from literax.storage.collection import default_collection_manager
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

class BenchmarkRequest(BaseModel):
    base_count: int = 50

class MatrixRequest(BaseModel):
    topic: str
    papers: List[Paper]

class MatrixExportRequest(BaseModel):
    matrix: LiteratureMatrix
    format: str = "markdown"

class GapRequest(BaseModel):
    topic: str
    papers: List[Paper]

@router.post("/correct", response_model=CorrectionResult, tags=["Fuzzy Search"], summary="Correct search query")
async def correct_query(req: CorrectRequest):
    """Corrects user query typos and computes fuzzy logic confidence score."""
    return fuzzy_engine.process_query(req.query)

@router.post("/search", response_model=List[Paper], tags=["Search & Aggregation"], summary="Search and aggregate literature")
async def search_literature(query: SearchQuery):
    """Searches across academic providers, deduplicates, and ranks by relevance."""
    # Process auto-correct if needed
    correction = fuzzy_engine.process_query(query.raw_query)
    effective_query = query.model_copy()
    if correction.action == "AUTO_CORRECTED":
        effective_query.raw_query = correction.corrected_query

    return await aggregator.search(effective_query)

@router.post("/analyze", response_model=PaperAnalysis, tags=["Synthesis & Analysis"], summary="Extract paper taxonomy")
async def analyze_paper(paper: Paper):
    """Extracts structured research taxonomy from paper metadata and abstract."""
    return await PaperAnalyzer.analyze(paper)

@router.post("/matrix", response_model=LiteratureMatrix, tags=["Literature Matrix"], summary="Generate literature review matrix")
async def generate_matrix(req: MatrixRequest):
    """Generates a structured comparative literature review matrix."""
    return LiteratureMatrixBuilder.build_matrix(req.topic, req.papers)

@router.post("/matrix/export", tags=["Literature Matrix"], summary="Export literature review matrix")
async def export_matrix(req: MatrixExportRequest):
    """Exports a literature matrix into Markdown, CSV, or BibTeX."""
    content = LiteratureMatrixBuilder.export(req.matrix, req.format)
    return {"format": req.format, "content": content}

@router.post("/gap", response_model=ResearchGapReport, tags=["Research Gap Finder"], summary="Identify research gaps")
async def find_research_gaps(req: GapRequest):
    """Identifies potential research gaps across a cluster of papers."""
    return ResearchGapFinder.find_gaps(req.topic, req.papers)

@router.get("/papers/{id}/citation", response_model=CitationResponse, tags=["Citations"], summary="Format academic citation")
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

# Collections API
@router.post("/collections/{user_id}/papers", tags=["Collections"], summary="Add paper to collection")
async def add_to_collection(user_id: str, paper: Paper):
    """Saves a paper into the user's personal collection."""
    added = default_collection_manager.add_paper(user_id, paper)
    return {
        "status": "added" if added else "already_exists",
        "total_saved": default_collection_manager.count(user_id)
    }

@router.get("/collections/{user_id}", response_model=List[Paper], tags=["Collections"], summary="Get user collection")
async def get_user_collection(user_id: str):
    """Retrieves all saved papers in user's collection."""
    return default_collection_manager.get_papers(user_id)

@router.delete("/collections/{user_id}/papers/{paper_id}", tags=["Collections"], summary="Remove paper from collection")
async def remove_from_collection(user_id: str, paper_id: str):
    """Removes a paper from user's collection."""
    removed = default_collection_manager.remove_paper(user_id, paper_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Paper not found in collection")
    return {"status": "removed", "total_saved": default_collection_manager.count(user_id)}

@router.get("/collections/{user_id}/export", tags=["Collections"], summary="Export user collection")
async def export_user_collection(user_id: str, format: str = "markdown"):
    """Exports user's collection to Markdown, CSV, or BibTeX."""
    exported = default_collection_manager.export_collection(user_id, export_format=format)
    return {"format": format, "content": exported}

# Benchmark API
@router.post("/benchmark/dedup", response_model=DedupBenchmarkResult, tags=["Benchmarking"], summary="Run deduplication benchmark")
async def run_deduplication_benchmark(req: BenchmarkRequest = BenchmarkRequest()):
    """Executes automated deduplication benchmark suite."""
    return DeduplicationBenchmarkSuite.run_benchmark(req.base_count)

# ==============================================================================
# Telegram Bot Webhook & Management Endpoints
# ==============================================================================

_bot_instance: Optional[Bot] = None
_dp_instance: Optional[Dispatcher] = None

def get_telegram_instances() -> tuple[Optional[Bot], Optional[Dispatcher]]:
    global _bot_instance, _dp_instance
    if _bot_instance is None and settings.bot_token:
        _bot_instance = Bot(token=settings.bot_token)
        _dp_instance = Dispatcher()
        from literax.bot.handlers import router as bot_router
        _dp_instance.include_router(bot_router)
    return _bot_instance, _dp_instance

@router.get("/telegram/status", tags=["Telegram Bot"], summary="Get Telegram bot connection status")
async def get_telegram_status():
    """Returns the current connection status of the Telegram Bot and Webhook configuration."""
    if not settings.bot_token:
        return {
            "configured": False,
            "status": "BOT_TOKEN is not configured in .env",
            "mode": settings.telegram_mode
        }

    bot, _ = get_telegram_instances()
    try:
        me = await bot.get_me()
        webhook_info = await bot.get_webhook_info()
        return {
            "configured": True,
            "bot": {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "can_join_groups": me.can_join_groups
            },
            "mode": settings.telegram_mode,
            "webhook": {
                "url": webhook_info.url,
                "has_custom_certificate": webhook_info.has_custom_certificate,
                "pending_update_count": webhook_info.pending_update_count,
                "last_error_message": webhook_info.last_error_message,
                "last_error_date": webhook_info.last_error_date
            }
        }
    except Exception as e:
        return {
            "configured": True,
            "status": "error_connecting_to_telegram",
            "error": str(e)
        }

@router.post("/telegram/webhook", tags=["Telegram Bot"], summary="Receive Telegram webhook update")
async def handle_telegram_webhook(
    update: Dict[str, Any],
    x_telegram_bot_api_secret_token: Optional[str] = Header(None)
):
    """Handles incoming webhook updates pushed from Telegram servers."""
    if not settings.bot_token:
        raise HTTPException(status_code=503, detail="Telegram bot is not configured on this server")

    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            raise HTTPException(status_code=403, detail="Invalid secret token")

    bot, dp = get_telegram_instances()
    if not bot or not dp:
        raise HTTPException(status_code=500, detail="Bot instances could not be initialized")

    try:
        telegram_update = Update.model_validate(update, context={"bot": bot})
        await dp.feed_update(bot, telegram_update)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process update: {str(e)}")

@router.post("/telegram/set-webhook", tags=["Telegram Bot"], summary="Register Webhook with Telegram")
async def set_telegram_webhook():
    """Registers the public webhook URL with Telegram servers."""
    if not settings.bot_token:
        raise HTTPException(status_code=503, detail="BOT_TOKEN is not configured")
    if not settings.telegram_webhook_url:
        raise HTTPException(status_code=400, detail="TELEGRAM_WEBHOOK_URL is not configured in .env")

    bot, _ = get_telegram_instances()
    try:
        success = await bot.set_webhook(
            url=settings.telegram_webhook_url,
            secret_token=settings.telegram_webhook_secret,
            drop_pending_updates=False
        )
        return {"success": success, "webhook_url": settings.telegram_webhook_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set webhook: {str(e)}")

@router.post("/telegram/delete-webhook", tags=["Telegram Bot"], summary="Delete Webhook (switch to polling)")
async def delete_telegram_webhook():
    """Removes webhook registration from Telegram (enables switching to polling)."""
    if not settings.bot_token:
        raise HTTPException(status_code=503, detail="BOT_TOKEN is not configured")

    bot, _ = get_telegram_instances()
    try:
        success = await bot.delete_webhook(drop_pending_updates=False)
        return {"success": success, "message": "Webhook removed. Polling mode can now be used."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")


