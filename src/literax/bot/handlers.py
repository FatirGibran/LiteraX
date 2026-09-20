from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode

from literax.nlp.fuzzy import FuzzyAutoCorrect
from literax.engine.aggregator import PaperAggregator
from literax.models import SearchQuery, Paper
from literax.synthesis.citation import CitationGenerator
from literax.synthesis.analyzer import PaperAnalyzer
from literax.synthesis.matrix import LiteratureMatrixBuilder
from literax.synthesis.gap_finder import ResearchGapFinder
from literax.bot.keyboards import get_confirmation_keyboard, get_paper_keyboard

router = Router()
fuzzy_engine = FuzzyAutoCorrect()
aggregator = PaperAggregator()

# In-memory session cache for demonstration
USER_SESSIONS = {}

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "🔬 *Welcome to LiteraX — AI Research Automation Bot*\n\n"
        "I can discover, analyze, and cite scientific papers from SINTA, Scopus, and global repositories.\n\n"
        "⚡ *Commands:*\n"
        "• `/search <query>` — Search papers with auto-typo correction\n"
        "• `/matrix <topic>` — Generate literature review matrix\n"
        "• `/gap <topic>` — Synthesize potential research gaps\n"
        "• `/cite <doi>` — Get formatted citation\n\n"
        "_Example:_ `/search machne lerning untk deteksi phising`"
    )
    await message.reply(welcome_text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("search"))
async def cmd_search(message: types.Message):
    raw_query = message.text.replace("/search", "").strip()
    if not raw_query:
        await message.reply("⚠️ Please provide a search query.\nExample: `/search deep learning for phishing`", parse_mode=ParseMode.MARKDOWN)
        return

    # Step 1: Fuzzy Auto-Correct
    correction = fuzzy_engine.process_query(raw_query)

    if correction.action == "PROMPT_USER":
        kb = get_confirmation_keyboard(correction.corrected_query, raw_query)
        await message.reply(
            f"🤔 *Did you mean:*\n_{correction.corrected_query}_\n\nConfidence: *{int(correction.overall_confidence * 100)}%*",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    search_term = correction.corrected_query if correction.action == "AUTO_CORRECTED" else raw_query
    info_msg = ""
    if correction.action == "AUTO_CORRECTED":
        info_msg = f"🔎 *Corrected Query:* `{correction.corrected_query}` (Confidence: {int(correction.overall_confidence*100)}%)\n\n"

    status_msg = await message.reply(f"{info_msg}⚡ Searching OpenAlex, Scopus, Crossref, and SINTA...", parse_mode=ParseMode.MARKDOWN)

    # Step 2: Multi-source search
    query_obj = SearchQuery(raw_query=search_term, limit=5)
    papers = await aggregator.search(query_obj)

    if not papers:
        await status_msg.edit_text(f"{info_msg}❌ No papers found for `{search_term}`.", parse_mode=ParseMode.MARKDOWN)
        return

    USER_SESSIONS[message.chat.id] = papers
    await send_paper_result(message, papers, index=0, edit_message=status_msg)

async def send_paper_result(message: types.Message, papers: list[Paper], index: int, edit_message: types.Message | None = None):
    paper = papers[index]
    authors_str = ", ".join([a.name for a in paper.authors[:2]]) if paper.authors else "Unknown"
    abstract_preview = (paper.abstract[:280] + "...") if paper.abstract else "Abstract not available in public preview."

    text = (
        f"📚 *SEARCH RESULTS ({index + 1}/{len(papers)})*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 *{paper.title}*\n"
        f"👤 *Authors:* {authors_str}\n"
        f"📅 *Year:* {paper.year or 'N/A'} | 🏛️ *Source:* {paper.source}\n"
        f"⭐ *Relevance:* {int(paper.composite_relevance * 100)}% | 🔗 *DOI:* `{paper.doi or 'N/A'}`\n\n"
        f"📝 *Abstract:*\n_{abstract_preview}_\n"
    )

    kb = get_paper_keyboard(paper.doi, index, len(papers))
    if edit_message:
        await edit_message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data.startswith("nav_page:"))
async def on_nav_page(callback: types.CallbackQuery):
    idx = int(callback.data.split(":")[1])
    papers = USER_SESSIONS.get(callback.message.chat.id, [])
    if 0 <= idx < len(papers):
        await send_paper_result(callback.message, papers, index=idx, edit_message=callback.message)
    await callback.answer()

@router.callback_query(F.data.startswith("act_cite:"))
async def on_cite(callback: types.CallbackQuery):
    doi = callback.data.split(":")[1]
    papers = USER_SESSIONS.get(callback.message.chat.id, [])
    target = next((p for p in papers if p.doi == doi), papers[0] if papers else None)
    if target:
        apa = CitationGenerator.to_apa(target)
        bib = CitationGenerator.to_bibtex(target)
        text = f"📖 *APA 7th:*\n`{apa}`\n\n📜 *BibTeX:*\n```bibtex\n{bib}\n```"
        await callback.message.reply(text, parse_mode=ParseMode.MARKDOWN)
    await callback.answer("Citation generated!")

@router.callback_query(F.data.startswith("act_ana:"))
async def on_analyze(callback: types.CallbackQuery):
    doi = callback.data.split(":")[1]
    papers = USER_SESSIONS.get(callback.message.chat.id, [])
    target = next((p for p in papers if p.doi == doi), papers[0] if papers else None)
    if target:
        analysis = PaperAnalyzer.heuristic_extract(target)
        text = (
            f"🔬 *Paper Analysis:* {analysis.title}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Objective:* {analysis.research_objective}\n"
            f"🛠️ *Methods:* {', '.join(analysis.algorithms_used)}\n"
            f"📊 *Dataset:* {analysis.dataset}\n"
            f"📈 *Key Findings:* {analysis.key_findings}\n"
            f"⚠️ *Limitations:* {analysis.limitations}"
        )
        await callback.message.reply(text, parse_mode=ParseMode.MARKDOWN)
    await callback.answer("Analysis complete!")

@router.message(Command("matrix"))
async def cmd_matrix(message: types.Message):
    topic = message.text.replace("/matrix", "").strip()
    if not topic:
        await message.reply("⚠️ Please provide a research topic.\nExample: `/matrix federated learning IoT`", parse_mode=ParseMode.MARKDOWN)
        return

    status_msg = await message.reply(f"📊 Synthesizing literature matrix for *{topic}*...", parse_mode=ParseMode.MARKDOWN)
    query_obj = SearchQuery(raw_query=topic, limit=5)
    papers = await aggregator.search(query_obj)

    if not papers:
        await status_msg.edit_text(f"❌ No papers found to construct matrix for `{topic}`.", parse_mode=ParseMode.MARKDOWN)
        return

    matrix = LiteratureMatrixBuilder.build_matrix(topic, papers)
    md_table = LiteratureMatrixBuilder.to_markdown(matrix)

    if len(md_table) > 4000:
        md_table = md_table[:3950] + "\n\n*(Matrix truncated for display limit)*"

    await status_msg.edit_text(md_table, parse_mode=ParseMode.MARKDOWN)
