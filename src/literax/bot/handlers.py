import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from literax.nlp.fuzzy import FuzzyAutoCorrect
from literax.engine.aggregator import PaperAggregator
from literax.models import SearchQuery, Paper
from literax.synthesis.citation import CitationGenerator
from literax.synthesis.analyzer import PaperAnalyzer
from literax.synthesis.matrix import LiteratureMatrixBuilder
from literax.synthesis.gap_finder import ResearchGapFinder
from literax.storage.collection import default_collection_manager
from literax.bot.keyboards import (
    get_confirmation_keyboard,
    get_paper_keyboard,
    get_export_format_keyboard,
    get_main_menu_keyboard
)

logger = logging.getLogger("literax.bot.handlers")
router = Router()
fuzzy_engine = FuzzyAutoCorrect()
aggregator = PaperAggregator()

# In-memory session cache for active search results: chat_id -> List[Paper]
USER_SESSIONS: dict[int, list[Paper]] = {}

class BotStates(StatesGroup):
    waiting_for_search_query = State()
    waiting_for_matrix_topic = State()
    waiting_for_gap_topic = State()

WELCOME_MESSAGE_TEXT = (
    "🔬 *Welcome to LiteraX — AI Academic Assistant*\n\n"
    "Selamat datang! Saya dapat menemukan, menganalisis, dan membuat sitasi ilmiah dari "
    "SINTA, Scopus, OpenAlex, Semantic Scholar, dan Crossref.\n\n"
    "⚡ *Menu Input & Perintah:*\n"
    "• `🔍 Cari Paper` atau `/search` / `/cari <topik>` — Pencarian multi-sumber dengan auto-koreksi typo\n"
    "• `📊 Literature Matrix` atau `/matrix <topik>` — Sintesis matriks komparasi literatur\n"
    "• `🔬 Research Gap` atau `/gap <topik>` — Identifikasi celah riset dan peluang baru\n"
    "• `📖 Sitasi` atau `/cite <doi>` — Format sitasi instan (APA 7th, BibTeX)\n"
    "• `📚 Paper Tersimpan` atau `/saved` — Akses dan ekspor koleksi riset Anda\n\n"
    "💡 *Tips Cepat:* Anda juga bisa langsung memilih tombol menu di bawah atau mengetik pertanyaan topik apa saja di chat!"
)

# ------------------------------------------------------------------------------
# Robust Messaging Helper (Fallback to plain text if Markdown fails)
# ------------------------------------------------------------------------------

async def safe_reply(message: types.Message, text: str, reply_markup=None, parse_mode=ParseMode.MARKDOWN):
    """Sends a message with Markdown formatting, falling back to plain text if parsing errors occur."""
    try:
        return await message.reply(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.warning("Markdown formatting failed (%s), sending as plain text fallback", e)
        return await message.reply(text, reply_markup=reply_markup, parse_mode=None)

# ------------------------------------------------------------------------------
# 1. Start & Help Handlers
# ------------------------------------------------------------------------------

@router.message(Command("start", "help", "bantuan"))
async def cmd_start(message: types.Message, state: FSMContext | None = None):
    logger.info("📩 User %s sent /start or /help", message.chat.id)
    if state:
        await state.clear()
    await safe_reply(
        message,
        WELCOME_MESSAGE_TEXT,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------------------------------------------------------------------
# 2. Main Menu Button Handlers
# ------------------------------------------------------------------------------

@router.message(F.text.in_(["🔍 Cari Paper", "🔍 Cari Riset"]))
async def on_menu_search(message: types.Message, state: FSMContext):
    logger.info("🔘 User %s clicked 'Cari Paper'", message.chat.id)
    await state.set_state(BotStates.waiting_for_search_query)
    await safe_reply(
        message,
        "🔍 *Pencarian Paper Ilmiah*\n\n"
        "Silakan ketik kata kunci, judul, atau topik riset yang ingin dicari:\n\n"
        "_Contoh:_ `pengaruh media sosial terhadap partisipasi pemilu`",
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(F.text.in_(["📚 Paper Tersimpan", "📚 Koleksi Saya"]))
async def on_menu_saved(message: types.Message, state: FSMContext):
    logger.info("🔘 User %s clicked 'Paper Tersimpan'", message.chat.id)
    await state.clear()
    await show_saved_collection(message)

@router.message(F.text == "📊 Literature Matrix")
async def on_menu_matrix(message: types.Message, state: FSMContext):
    logger.info("🔘 User %s clicked 'Literature Matrix'", message.chat.id)
    await state.set_state(BotStates.waiting_for_matrix_topic)
    await safe_reply(
        message,
        "📊 *Pembuatan Literature Matrix*\n\n"
        "Silakan ketik topik riset untuk disusun matriks perbandingan metodologinya:\n\n"
        "_Contoh:_ `phishing detection machine learning`",
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(F.text == "🔬 Research Gap")
async def on_menu_gap(message: types.Message, state: FSMContext):
    logger.info("🔘 User %s clicked 'Research Gap'", message.chat.id)
    await state.set_state(BotStates.waiting_for_gap_topic)
    await safe_reply(
        message,
        "🔬 *Analisis Research Gap*\n\n"
        "Silakan ketik topik riset untuk dianalisis peluang dan celah riset barunya:\n\n"
        "_Contoh:_ `blockchain for supply chain traceability`",
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(F.text.in_(["❓ Panduan & Bantuan", "❓ Bantuan", "ℹ️ Panduan"]))
async def on_menu_help(message: types.Message, state: FSMContext):
    if state:
        await state.clear()
    await safe_reply(
        message,
        WELCOME_MESSAGE_TEXT,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

# ------------------------------------------------------------------------------
# 3. FSM State Input Handlers
# ------------------------------------------------------------------------------

@router.message(BotStates.waiting_for_search_query)
async def on_state_search_query(message: types.Message, state: FSMContext):
    await state.clear()
    query = (message.text or "").strip()
    if query:
        await process_search_query(message, query)

@router.message(BotStates.waiting_for_matrix_topic)
async def on_state_matrix_topic(message: types.Message, state: FSMContext):
    await state.clear()
    topic = (message.text or "").strip()
    if topic:
        await execute_matrix(message, topic)

@router.message(BotStates.waiting_for_gap_topic)
async def on_state_gap_topic(message: types.Message, state: FSMContext):
    await state.clear()
    topic = (message.text or "").strip()
    if topic:
        await execute_gap(message, topic)

# ------------------------------------------------------------------------------
# 4. Search Commands & Logic
# ------------------------------------------------------------------------------

@router.message(Command("search", "cari"))
async def cmd_search(message: types.Message, state: FSMContext | None = None):
    if state:
        await state.clear()

    text = message.text or ""
    parts = text.split(maxsplit=1)
    raw_query = parts[1].strip() if len(parts) > 1 else ""

    if not raw_query:
        if state:
            await state.set_state(BotStates.waiting_for_search_query)
        await safe_reply(
            message,
            "⚠️ Silakan masukkan kata kunci atau topik pencarian.\n\n"
            "_Contoh:_ `/cari tentang soekarno`\n"
            "Atau langsung ketik kata kuncinya di sini.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    await process_search_query(message, raw_query)

async def process_search_query(message: types.Message, raw_query: str):
    logger.info("🔎 Searching query from user %s: '%s'", message.chat.id, raw_query)
    try:
        # Step 1: Fuzzy Auto-Correct
        correction = fuzzy_engine.process_query(raw_query)

        if correction.action == "PROMPT_USER":
            kb = get_confirmation_keyboard(correction.corrected_query, raw_query)
            await safe_reply(
                message,
                f"🤔 *Maksud Anda:*\n_{correction.corrected_query}_\n\nKeyakinan: *{int(correction.overall_confidence * 100)}%*",
                reply_markup=kb,
                parse_mode=ParseMode.MARKDOWN
            )
            return

        search_term = correction.corrected_query if correction.action == "AUTO_CORRECTED" else raw_query
        await execute_search(message, search_term, correction if correction.action == "AUTO_CORRECTED" else None)
    except Exception as e:
        logger.exception("Error processing search: %s", e)
        await safe_reply(message, f"❌ Terjadi kesalahan saat memproses pencarian: {str(e)}", parse_mode=None)

async def execute_search(message: types.Message, search_term: str, correction=None, edit_message: types.Message | None = None):
    info_msg = ""
    if correction:
        info_msg = f"🔎 *Koreksi Kata Kunci:* `{correction.corrected_query}` (Akurasi: {int(correction.overall_confidence * 100)}%)\n\n"

    prompt_text = f"{info_msg}⚡ Mencari di OpenAlex, Scopus, Crossref, dan SINTA..."
    if edit_message:
        status_msg = edit_message
        try:
            await edit_message.edit_text(prompt_text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await edit_message.edit_text(prompt_text, parse_mode=None)
    else:
        status_msg = await safe_reply(message, prompt_text, parse_mode=ParseMode.MARKDOWN)

    try:
        # Step 2: Multi-source search
        query_obj = SearchQuery(raw_query=search_term, limit=5)
        papers = await aggregator.search(query_obj)

        if not papers:
            not_found_text = f"{info_msg}❌ Tidak ditemukan paper ilmiah untuk `{search_term}`."
            try:
                await status_msg.edit_text(not_found_text, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await status_msg.edit_text(not_found_text, parse_mode=None)
            return

        chat_id = message.chat.id
        USER_SESSIONS[chat_id] = papers
        await send_paper_result(message, papers, index=0, edit_message=status_msg)
    except Exception as e:
        logger.exception("Error executing paper search: %s", e)
        err_text = f"❌ Terjadi kesalahan saat mencari literatur: {str(e)}"
        try:
            await status_msg.edit_text(err_text, parse_mode=None)
        except Exception:
            await safe_reply(message, err_text, parse_mode=None)

async def send_paper_result(message: types.Message, papers: list[Paper], index: int, edit_message: types.Message | None = None):
    paper = papers[index]
    authors_str = ", ".join([a.name for a in paper.authors[:2]]) if paper.authors else "Unknown"
    abstract_preview = (paper.abstract[:280] + "...") if paper.abstract else "Abstrak belum tersedia di ringkasan publik."

    text = (
        f"📚 *HASIL PENCARIAN ({index + 1}/{len(papers)})*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 *{paper.title}*\n"
        f"👤 *Penulis:* {authors_str}\n"
        f"📅 *Tahun:* {paper.year or 'N/A'} | 🏛️ *Sumber:* {paper.source}\n"
        f"⭐ *Relevansi:* {int(paper.composite_relevance * 100)}% | 🔗 *DOI:* `{paper.doi or 'N/A'}`\n\n"
        f"📝 *Abstrak:*\n_{abstract_preview}_\n"
    )

    kb = get_paper_keyboard(paper.doi or paper.id, index, len(papers))
    if edit_message:
        try:
            await edit_message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            # Fallback without markdown if title/abstract has entity conflicts
            fallback_text = (
                f"📚 HASIL PENCARIAN ({index + 1}/{len(papers)})\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📄 {paper.title}\n"
                f"👤 Penulis: {authors_str}\n"
                f"📅 Tahun: {paper.year or 'N/A'} | 🏛️ Sumber: {paper.source}\n"
                f"⭐ Relevansi: {int(paper.composite_relevance * 100)}% | 🔗 DOI: {paper.doi or 'N/A'}\n\n"
                f"📝 Abstrak:\n{abstract_preview}\n"
            )
            await edit_message.edit_text(fallback_text, reply_markup=kb, parse_mode=None)
    else:
        await safe_reply(message, text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# ------------------------------------------------------------------------------
# 5. Matrix & Gap Analysis
# ------------------------------------------------------------------------------

@router.message(Command("matrix", "matriks"))
async def cmd_matrix(message: types.Message, state: FSMContext | None = None):
    if state:
        await state.clear()
    text = message.text or ""
    parts = text.split(maxsplit=1)
    topic = parts[1].strip() if len(parts) > 1 else ""
    if not topic:
        if state:
            await state.set_state(BotStates.waiting_for_matrix_topic)
        await safe_reply(message, "⚠️ Silakan masukkan topik riset.\n_Contoh:_ `/matrix federated learning IoT`", parse_mode=ParseMode.MARKDOWN)
        return
    await execute_matrix(message, topic)

async def execute_matrix(message: types.Message, topic: str):
    status_msg = await safe_reply(message, f"📊 Menyusun literature matrix untuk *{topic}*...", parse_mode=ParseMode.MARKDOWN)
    query_obj = SearchQuery(raw_query=topic, limit=5)
    papers = await aggregator.search(query_obj)

    if not papers:
        await status_msg.edit_text(f"❌ Tidak ditemukan paper untuk menyusun matriks `{topic}`.", parse_mode=None)
        return

    matrix = LiteratureMatrixBuilder.build_matrix(topic, papers)
    md_table = LiteratureMatrixBuilder.to_markdown(matrix)

    if len(md_table) > 4000:
        md_table = md_table[:3950] + "\n\n*(Matriks dipotong karena batas karakter Telegram)*"

    try:
        await status_msg.edit_text(md_table, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await status_msg.edit_text(md_table, parse_mode=None)

@router.message(Command("gap", "peluang", "celah"))
async def cmd_gap(message: types.Message, state: FSMContext | None = None):
    if state:
        await state.clear()
    text = message.text or ""
    parts = text.split(maxsplit=1)
    topic = parts[1].strip() if len(parts) > 1 else ""
    if not topic:
        if state:
            await state.set_state(BotStates.waiting_for_gap_topic)
        await safe_reply(message, "⚠️ Silakan masukkan topik riset.\n_Contoh:_ `/gap phishing detection zero day`", parse_mode=ParseMode.MARKDOWN)
        return
    await execute_gap(message, topic)

async def execute_gap(message: types.Message, topic: str):
    status_msg = await safe_reply(message, f"🔍 Menganalisis research gap untuk *{topic}*...", parse_mode=ParseMode.MARKDOWN)
    query_obj = SearchQuery(raw_query=topic, limit=5)
    papers = await aggregator.search(query_obj)

    if not papers:
        await status_msg.edit_text(f"❌ Tidak ditemukan paper untuk menganalisis gap `{topic}`.", parse_mode=None)
        return

    report = ResearchGapFinder.find_gaps(topic, papers)
    lines = [f"🔬 *Analisis Research Gap: {report.topic}*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for idx, gap in enumerate(report.gaps, 1):
        lines.append(f"📌 *{idx}. [{gap.category}] {gap.title}*\n{gap.description}\n")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3950] + "\n..."
    try:
        await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await status_msg.edit_text(text, parse_mode=None)

# ------------------------------------------------------------------------------
# 6. Citations & Collections
# ------------------------------------------------------------------------------

@router.message(Command("cite", "sitasi", "kutip"))
async def cmd_cite(message: types.Message):
    text = message.text or ""
    parts = text.split(maxsplit=1)
    raw = parts[1].strip() if len(parts) > 1 else ""
    if not raw:
        await safe_reply(message, "⚠️ Masukkan DOI atau identifier paper.\n_Contoh:_ `/cite 10.1016/j.cose.2024.103982`", parse_mode=ParseMode.MARKDOWN)
        return

    status_msg = await safe_reply(message, "⏳ Menyusun sitasi otomatis via DOI...", parse_mode=ParseMode.MARKDOWN)
    resolved_citation = await CitationGenerator.resolve_doi_citation(raw, style="apa")
    bib_citation = await CitationGenerator.resolve_doi_citation(raw, style="bibtex")

    if resolved_citation:
        res_text = f"📖 *APA 7th:*\n`{resolved_citation}`\n\n📜 *BibTeX:*\n```bibtex\n{bib_citation or ''}\n```"
    else:
        paper = Paper(id=raw, title="Academic Publication", doi=raw, source="Crossref")
        apa = CitationGenerator.to_apa(paper)
        bib = CitationGenerator.to_bibtex(paper)
        res_text = f"📖 *APA 7th (Heuristik):*\n`{apa}`\n\n📜 *BibTeX:*\n```bibtex\n{bib}\n```"

    try:
        await status_msg.edit_text(res_text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await status_msg.edit_text(res_text, parse_mode=None)

@router.message(Command("save", "simpan"))
async def cmd_save(message: types.Message):
    chat_id = message.chat.id
    papers = USER_SESSIONS.get(chat_id, [])
    if not papers:
        await safe_reply(message, "⚠️ Belum ada paper aktif di sesi ini. Cari paper terlebih dahulu dengan tombol `🔍 Cari Paper` atau `/cari <topik>`.", parse_mode=ParseMode.MARKDOWN)
        return

    target = papers[0]
    added = default_collection_manager.add_paper(str(chat_id), target)
    total = default_collection_manager.count(str(chat_id))
    if added:
        await safe_reply(message, f"💾 *Tersimpan di koleksi:*\n_{target.title}_\n\nTotal paper tersimpan: *{total}*", parse_mode=ParseMode.MARKDOWN)
    else:
        await safe_reply(message, f"ℹ️ Paper sudah ada di koleksi Anda.\nTotal tersimpan: *{total}*", parse_mode=ParseMode.MARKDOWN)

@router.message(Command("saved", "tersimpan", "koleksi"))
async def cmd_saved(message: types.Message):
    await show_saved_collection(message)

async def show_saved_collection(message: types.Message):
    chat_id = str(message.chat.id)
    text_content = message.text or ""
    raw_args = text_content.replace("/saved", "").replace("/tersimpan", "").replace("/koleksi", "").strip().lower()

    if raw_args.startswith("export"):
        parts = raw_args.split()
        fmt = parts[1] if len(parts) > 1 else "markdown"
        exported = default_collection_manager.export_collection(chat_id, export_format=fmt)
        if not exported.strip():
            await safe_reply(message, "📭 Koleksi Anda saat ini masih kosong.", parse_mode=ParseMode.MARKDOWN)
            return
        if len(exported) > 3900:
            exported = exported[:3900] + "\n...(dipotong)"
        await safe_reply(message, f"📑 *Koleksi Riset ({fmt.upper()}):*\n\n```\n{exported}\n```", parse_mode=ParseMode.MARKDOWN)
        return

    papers = default_collection_manager.get_papers(chat_id)
    if not papers:
        await safe_reply(message, "📭 Koleksi paper Anda masih kosong.\nCari paper lalu tekan tombol *💾 Save* pada hasil pencarian.", parse_mode=ParseMode.MARKDOWN)
        return

    lines = [f"📚 *Koleksi Paper Anda ({len(papers)})*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for idx, p in enumerate(papers[:10], 1):
        year_str = f"({p.year})" if p.year else ""
        lines.append(f"{idx}. *{p.title}* {year_str}\n   🔗 `{p.doi or p.id}`")

    if len(papers) > 10:
        lines.append(f"\n_...dan {len(papers) - 10} paper lainnya._")

    lines.append("\n💡 *Ekspor cepat:*")
    kb = get_export_format_keyboard()
    await safe_reply(message, "\n".join(lines), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# ------------------------------------------------------------------------------
# 7. Fallback Direct Natural Text Search
# ------------------------------------------------------------------------------

@router.message(F.text)
async def fallback_text_search(message: types.Message, state: FSMContext | None = None):
    text = (message.text or "").strip()
    # Ignore slash commands that were not recognized
    if text.startswith("/"):
        return
    # Process regular text directly as search query
    await process_search_query(message, text)

# ------------------------------------------------------------------------------
# 8. Callback Query Handlers
# ------------------------------------------------------------------------------

@router.callback_query(F.data.startswith("search_corr:"))
async def on_search_corrected(callback: types.CallbackQuery):
    corr_term = callback.data.split(":", 1)[1]
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await execute_search(callback.message, corr_term, edit_message=callback.message)
    await callback.answer()

@router.callback_query(F.data.startswith("search_raw:"))
async def on_search_raw(callback: types.CallbackQuery):
    raw_term = callback.data.split(":", 1)[1]
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await execute_search(callback.message, raw_term, edit_message=callback.message)
    await callback.answer()

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
    target = next((p for p in papers if p.doi == doi or p.id == doi), papers[0] if papers else None)
    if target:
        apa = CitationGenerator.to_apa(target)
        bib = CitationGenerator.to_bibtex(target)
        text = f"📖 *APA 7th:*\n`{apa}`\n\n📜 *BibTeX:*\n```bibtex\n{bib}\n```"
        await safe_reply(callback.message, text, parse_mode=ParseMode.MARKDOWN)
    await callback.answer("Sitasi berhasil dibuat!")

@router.callback_query(F.data.startswith("act_ana:"))
async def on_analyze(callback: types.CallbackQuery):
    doi = callback.data.split(":")[1]
    papers = USER_SESSIONS.get(callback.message.chat.id, [])
    target = next((p for p in papers if p.doi == doi or p.id == doi), papers[0] if papers else None)
    if target:
        analysis = PaperAnalyzer.heuristic_extract(target)
        text = (
            f"🔬 *Analisis Paper:* {analysis.title}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Tujuan Riset:* {analysis.research_objective}\n"
            f"🛠️ *Metodologi:* {', '.join(analysis.algorithms_used)}\n"
            f"📊 *Dataset:* {analysis.dataset}\n"
            f"📈 *Temuan Utama:* {analysis.key_findings}\n"
            f"⚠️ *Limitasi:* {analysis.limitations}"
        )
        await safe_reply(callback.message, text, parse_mode=ParseMode.MARKDOWN)
    await callback.answer("Analisis selesai!")

@router.callback_query(F.data.startswith("act_save:"))
async def on_save_callback(callback: types.CallbackQuery):
    doi_or_id = callback.data.split(":")[1]
    chat_id = str(callback.message.chat.id)
    papers = USER_SESSIONS.get(callback.message.chat.id, [])
    target = next((p for p in papers if p.doi == doi_or_id or p.id == doi_or_id), papers[0] if papers else None)

    if target:
        added = default_collection_manager.add_paper(chat_id, target)
        total = default_collection_manager.count(chat_id)
        if added:
            await callback.answer(f"💾 Tersimpan ke koleksi! (Total: {total})", show_alert=False)
        else:
            await callback.answer(f"ℹ️ Sudah ada di koleksi! (Total: {total})", show_alert=False)
    else:
        await callback.answer("⚠️ Tidak dapat menyimpan paper dari sesi ini.", show_alert=True)

@router.callback_query(F.data.startswith("exp_fmt:"))
async def on_export_format_callback(callback: types.CallbackQuery):
    fmt = callback.data.split(":")[1]
    chat_id = str(callback.message.chat.id)
    exported = default_collection_manager.export_collection(chat_id, export_format=fmt)
    if not exported.strip():
        await callback.answer("Koleksi masih kosong.", show_alert=True)
        return
    if len(exported) > 3900:
        exported = exported[:3900] + "\n...(dipotong)"
    await safe_reply(callback.message, f"📑 *Ekspor Koleksi ({fmt.upper()}):*\n\n```\n{exported}\n```", parse_mode=ParseMode.MARKDOWN)
    await callback.answer()
