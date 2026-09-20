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
from literax.storage.collection import default_collection_manager
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

@router.message(Command("gap"))
async def cmd_gap(message: types.Message):
    topic = message.text.replace("/gap", "").strip()
    if not topic:
        await message.reply("⚠️ Please provide a research topic.\nExample: `/gap phishing detection zero day`", parse_mode=ParseMode.MARKDOWN)
        return

    status_msg = await message.reply(f"🔍 Analyzing research gaps for *{topic}*...", parse_mode=ParseMode.MARKDOWN)
    query_obj = SearchQuery(raw_query=topic, limit=5)
    papers = await aggregator.search(query_obj)

    if not papers:
        await status_msg.edit_text(f"❌ No papers found to analyze gaps for `{topic}`.", parse_mode=ParseMode.MARKDOWN)
        return

    report = ResearchGapFinder.find_gaps(topic, papers)
    lines = [f"🔬 *Research Gap Analysis: {report.topic}*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for idx, gap in enumerate(report.gaps, 1):
        lines.append(f"📌 *{idx}. [{gap.category}] {gap.title}*\n{gap.description}\n")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3950] + "\n..."
    await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("cite"))
async def cmd_cite(message: types.Message):
    raw = message.text.replace("/cite", "").strip()
    if not raw:
        await message.reply("⚠️ Please provide a DOI or identifier.\nExample: `/cite 10.1016/j.cose.2024.103982`", parse_mode=ParseMode.MARKDOWN)
        return

    status_msg = await message.reply("⏳ Resolving citation via DOI authority...", parse_mode=ParseMode.MARKDOWN)
    resolved_citation = await CitationGenerator.resolve_doi_citation(raw, style="apa")
    bib_citation = await CitationGenerator.resolve_doi_citation(raw, style="bibtex")

    if resolved_citation:
        text = f"📖 *APA 7th:*\n`{resolved_citation}`\n\n📜 *BibTeX:*\n```bibtex\n{bib_citation or ''}\n```"
    else:
        paper = Paper(id=raw, title="Academic Publication", doi=raw, source="Crossref")
        apa = CitationGenerator.to_apa(paper)
        bib = CitationGenerator.to_bibtex(paper)
        text = f"📖 *APA 7th (Heuristic):*\n`{apa}`\n\n📜 *BibTeX:*\n```bibtex\n{bib}\n```"

    await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)

@router.message(Command("save"))
async def cmd_save(message: types.Message):
    chat_id = message.chat.id
    papers = USER_SESSIONS.get(chat_id, [])
    if not papers:
        await message.reply("⚠️ No recently searched papers found in this session. Search for papers first with `/search <topic>`.", parse_mode=ParseMode.MARKDOWN)
        return

    target = papers[0]
    added = default_collection_manager.add_paper(str(chat_id), target)
    total = default_collection_manager.count(str(chat_id))
    if added:
        await message.reply(f"💾 *Saved to collection:*\n_{target.title}_\n\nTotal saved papers: *{total}*", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply(f"ℹ️ Paper is already in your collection.\nTotal saved: *{total}*", parse_mode=ParseMode.MARKDOWN)

@router.message(Command("saved"))
async def cmd_saved(message: types.Message):
    chat_id = str(message.chat.id)
    raw_args = message.text.replace("/saved", "").strip().lower()

    if raw_args.startswith("export"):
        parts = raw_args.split()
        fmt = parts[1] if len(parts) > 1 else "markdown"
        exported = default_collection_manager.export_collection(chat_id, export_format=fmt)
        if not exported.strip():
            await message.reply("📭 Your collection is currently empty.", parse_mode=ParseMode.MARKDOWN)
            return
        if len(exported) > 3900:
            exported = exported[:3900] + "\n...(truncated)"
        await message.reply(f"📑 *Exported Collection ({fmt.upper()}):*\n\n```\n{exported}\n```", parse_mode=ParseMode.MARKDOWN)
        return

    papers = default_collection_manager.get_papers(chat_id)
    if not papers:
        await message.reply("📭 Your personal collection is empty.\nUse `/search` and click *Save* on any paper.", parse_mode=ParseMode.MARKDOWN)
        return

    lines = [f"📚 *Your Saved Papers ({len(papers)})*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for idx, p in enumerate(papers[:10], 1):
        year_str = f"({p.year})" if p.year else ""
        lines.append(f"{idx}. *{p.title}* {year_str}\n   🔗 `{p.doi or p.id}`")

    if len(papers) > 10:
        lines.append(f"\n_...and {len(papers) - 10} more papers._")

    lines.append("\n💡 *Export with:* `/saved export bibtex` or `/saved export csv`")
    await message.reply("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
