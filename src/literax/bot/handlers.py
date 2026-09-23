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
from literax.synthesis.brainstormer import ResearchBrainstormer
from literax.storage.collection import default_collection_manager
from literax.nlp.normalizer import QueryNormalizer
from literax.bot.keyboards import (
    get_confirmation_keyboard,
    get_paper_keyboard,
    get_filter_selection_keyboard,
    get_export_format_keyboard,
    get_main_menu_keyboard
)

logger = logging.getLogger("literax.bot.handlers")
router = Router()
fuzzy_engine = FuzzyAutoCorrect()
aggregator = PaperAggregator()

# In-memory session cache for active search results: chat_id -> List[Paper]
USER_SESSIONS: dict[int, list[Paper]] = {}
# In-memory context for search parameters: chat_id -> {"query": str, "filter": str, "filters": dict}
USER_SEARCH_CONTEXT: dict[int, dict] = {}

class BotStates(StatesGroup):
    waiting_for_search_query = State()
    waiting_for_matrix_topic = State()
    waiting_for_gap_topic = State()
    waiting_for_brainstorm_topic = State()

WELCOME_MESSAGE_TEXT = (
    "🔬 *Welcome to LiteraX — AI Academic Assistant*\n\n"
    "Selamat datang! Saya dapat menemukan, menganalisis, dan membuat sitasi ilmiah dari "
    "SINTA, Scopus, OpenAlex, Semantic Scholar, dan Crossref.\n\n"
    "⚡ *Menu Input & Perintah:*\n"
    "• `🔍 Cari Paper` atau `/search` / `/cari <topik>` — Pencarian multi-sumber dengan auto-koreksi & direct links\n"
    "• `🏛️ Scopus` atau `/scopus <topik>` — Pencarian khusus paper internasional terindeks Scopus\n"
    "• `🇮🇩 SINTA` atau `/sinta <topik>` — Pencarian khusus jurnal nasional terakreditasi SINTA / GARUDA\n"
    "• `🎯 Filter Indeks` atau `/filter` — Atur filter indeks publikasi atau kategori Open Access\n"
    "• `💡 Brainstorm Riset` atau `/brainstorm <topik>` — Rumusan masalah, ide judul inovatif, dataset, dan kebaruan (novelty)\n"
    "• `📊 Literature Matrix` atau `/matrix <topik>` — Sintesis matriks komparasi metodologi\n"
    "• `🔬 Research Gap` atau `/gap <topik>` — Identifikasi celah riset dan peluang novelty baru\n"
    "• `📖 Sitasi` atau `/cite <doi>` — Format sitasi instan (APA 7th, BibTeX)\n"
    "• `📚 Paper Tersimpan` atau `/saved` — Akses dan ekspor koleksi riset Anda\n\n"
    "💡 *Tips Cepat:* Anda juga bisa langsung mengetik `scopus: <topik>` atau `sinta: <topik>` di chat!"
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
    USER_SEARCH_CONTEXT[message.chat.id] = {"filter": "all", "filters": {}}
    await safe_reply(
        message,
        "🔍 *Pencarian Paper Ilmiah (Semua Indeks)*\n\n"
        "Silakan ketik kata kunci, judul, atau topik riset yang ingin dicari:\n\n"
        "_Contoh:_ `pengaruh media sosial terhadap partisipasi pemilu`",
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(F.text.in_(["🏛️ Cari Scopus", "🏛️ Scopus"]))
async def on_menu_scopus(message: types.Message, state: FSMContext):
    logger.info("🔘 User %s clicked 'Cari Scopus'", message.chat.id)
    await state.set_state(BotStates.waiting_for_search_query)
    USER_SEARCH_CONTEXT[message.chat.id] = {"filter": "scopus", "filters": {"providers": ["scopus"]}}
    await safe_reply(
        message,
        "🏛️ *Pencarian Khusus Scopus*\n\n"
        "Filter aktif: *🏛️ SCOPUS (Internasional Bereputasi)*\n"
        "Silakan ketik kata kunci atau topik riset yang ingin dicari:\n\n"
        "_Contoh:_ `zero trust architecture cloud security`",
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(F.text.in_(["🇮🇩 Cari SINTA", "🇮🇩 SINTA", "🇮🇩 SINTA / GARUDA"]))
async def on_menu_sinta(message: types.Message, state: FSMContext):
    logger.info("🔘 User %s clicked 'Cari SINTA'", message.chat.id)
    await state.set_state(BotStates.waiting_for_search_query)
    USER_SEARCH_CONTEXT[message.chat.id] = {"filter": "sinta", "filters": {"providers": ["sinta"]}}
    await safe_reply(
        message,
        "🇮🇩 *Pencarian Khusus SINTA / GARUDA*\n\n"
        "Filter aktif: *🇮🇩 SINTA / GARUDA (Jurnal Nasional Terakreditasi)*\n"
        "Silakan ketik kata kunci atau topik riset yang ingin dicari:\n\n"
        "_Contoh:_ `sistem pendukung keputusan pemilihan dosen berprestasi`",
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(F.text.in_(["🎯 Filter & Kategori", "🎯 Filter Indeks & Kategori", "🎯 Filter Indeks", "🎯 Kategori"]))
async def on_menu_filter(message: types.Message):
    logger.info("🔘 User %s clicked 'Filter & Kategori'", message.chat.id)
    chat_id = message.chat.id
    current_flt = USER_SEARCH_CONTEXT.get(chat_id, {}).get("filter", "all")
    kb = get_filter_selection_keyboard(active_filter=current_flt)
    await safe_reply(
        message,
        "🎯 *Pengaturan Filter Indeks & Kategori Riset*\n\n"
        "Pilih indeks publikasi atau kategori untuk memfokuskan pencarian Anda:\n\n"
        "• 🏛️ *Scopus*: Jurnal & prosiding internasional bereputasi\n"
        "• 🇮🇩 *SINTA / GARUDA*: Jurnal nasional terakreditasi Kemendikbudristek\n"
        "• 📖 *OpenAlex*: Repositori bibliometrik global terbuka\n"
        "• 🔓 *Open Access*: Khusus artikel gratis dengan akses PDF langsung\n"
        "• 📅 *Terbaru*: Khusus publikasi mutakhir (>= 2023)\n\n"
        f"Filter aktif saat ini: *{current_flt.upper()}*",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(F.text.in_(["💡 Brainstorm Riset", "💡 Brainstorm Ide Riset", "💡 Brainstorming", "💡 Ide Riset"]))
async def on_menu_brainstorm(message: types.Message, state: FSMContext):
    logger.info("🔘 User %s clicked 'Brainstorm Riset'", message.chat.id)
    await state.set_state(BotStates.waiting_for_brainstorm_topic)
    await safe_reply(
        message,
        "💡 *AI Research Brainstorming & Ideation*\n\n"
        "Silakan ketik topik atau ide umum yang ingin Anda kembangkan menjadi judul riset berbobot:\n\n"
        "_Contoh:_ `deteksi hoaks machine learning` atau `federated learning privasi IoT`\n\n"
        "AI akan menyusun rumusan masalah, 3 rekomendasi judul paper/skripsi, metodologi mutakhir, dataset benchmark, dan reasoning potensi novelty!",
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

@router.message(BotStates.waiting_for_brainstorm_topic)
async def on_state_brainstorm_topic(message: types.Message, state: FSMContext):
    await state.clear()
    topic = (message.text or "").strip()
    if topic:
        await execute_brainstorm(message, topic)

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

@router.message(Command("filter", "indeks", "sumber"))
async def cmd_filter(message: types.Message):
    logger.info("🎯 User %s called /filter", message.chat.id)
    chat_id = message.chat.id
    current_flt = USER_SEARCH_CONTEXT.get(chat_id, {}).get("filter", "all")
    kb = get_filter_selection_keyboard(active_filter=current_flt)
    await safe_reply(
        message,
        "🎯 *Pengaturan Filter Indeks & Kategori*\n\n"
        "Pilih indeks atau kriteria yang Anda inginkan untuk memfokuskan hasil riset:\n\n"
        "• 🏛️ *Scopus*: Publikasi jurnal & prosiding internasional bereputasi\n"
        "• 🇮🇩 *SINTA*: Jurnal terakreditasi nasional Indonesia (GARUDA / SINTA)\n"
        "• 📖 *OpenAlex*: Repositori bibliografi terbuka universal\n"
        "• 🔓 *Open Access*: Artikel dengan akses dokumen penuh (Direct PDF)\n"
        "• 📅 *Terbaru*: Khusus publikasi tahun 2023 ke atas\n\n"
        "💡 *Tips:* Anda juga dapat menggunakan perintah langsung seperti:\n"
        "`/scopus <topik>` atau `/sinta <topik>`\n"
        "atau ketik langsung di chat: `scopus: <topik>`",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )

@router.message(Command("scopus"))
async def cmd_scopus(message: types.Message, state: FSMContext | None = None):
    logger.info("🏛️ User %s called /scopus", message.chat.id)
    if state:
        await state.clear()
    text = message.text or ""
    parts = text.split(maxsplit=1)
    raw_query = parts[1].strip() if len(parts) > 1 else ""
    if not raw_query:
        if state:
            await state.set_state(BotStates.waiting_for_search_query)
        USER_SEARCH_CONTEXT[message.chat.id] = {"filter": "scopus", "filters": {"providers": ["scopus"]}}
        await safe_reply(
            message,
            "🏛️ *Pencarian Khusus Scopus*\n\nSilakan ketik topik riset yang ingin dicari di Scopus:\n_Contoh:_ `/scopus machine learning cybersecurity`",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    await process_search_query(message, raw_query, extra_filters={"providers": ["scopus"]}, active_filter_key="scopus")

@router.message(Command("sinta", "garuda"))
async def cmd_sinta(message: types.Message, state: FSMContext | None = None):
    logger.info("🇮🇩 User %s called /sinta", message.chat.id)
    if state:
        await state.clear()
    text = message.text or ""
    parts = text.split(maxsplit=1)
    raw_query = parts[1].strip() if len(parts) > 1 else ""
    if not raw_query:
        if state:
            await state.set_state(BotStates.waiting_for_search_query)
        USER_SEARCH_CONTEXT[message.chat.id] = {"filter": "sinta", "filters": {"providers": ["sinta"]}}
        await safe_reply(
            message,
            "🇮🇩 *Pencarian Khusus SINTA / GARUDA*\n\nSilakan ketik topik riset yang ingin dicari di jurnal SINTA:\n_Contoh:_ `/sinta sistem pendukung keputusan`",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    await process_search_query(message, raw_query, extra_filters={"providers": ["sinta"]}, active_filter_key="sinta")

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

async def process_search_query(
    message: types.Message,
    raw_query: str,
    extra_filters: dict | None = None,
    active_filter_key: str | None = None
):
    logger.info("🔎 Searching query from user %s: '%s' (extra_filters=%s)", message.chat.id, raw_query, extra_filters)
    try:
        # Step 0: Extract syntax filters (e.g. scopus:, sinta:, oa:, year:2024)
        clean_query, extracted_filters = QueryNormalizer.extract_filters(raw_query)

        saved_ctx = USER_SEARCH_CONTEXT.get(message.chat.id, {})
        saved_flt = saved_ctx.get("filter", "all")

        # Determine effective filters and active_filter_key
        if extracted_filters:
            merged_filters = {**(extra_filters or {}), **extracted_filters}
            flt_key = active_filter_key
            if not flt_key:
                if "providers" in merged_filters and merged_filters["providers"]:
                    p = merged_filters["providers"][0]
                    flt_key = "sinta" if p in ["sinta", "garuda"] else p
                elif merged_filters.get("open_access_only"):
                    flt_key = "oa"
                elif merged_filters.get("year_start"):
                    flt_key = "recent"
                else:
                    flt_key = "all"
        else:
            if extra_filters is not None:
                merged_filters = extra_filters
                flt_key = active_filter_key or "all"
            elif saved_flt and saved_flt != "all":
                merged_filters = {}
                if saved_flt in ["scopus", "sinta", "openalex"]:
                    merged_filters["providers"] = [saved_flt]
                elif saved_flt == "oa":
                    merged_filters["open_access_only"] = True
                elif saved_flt == "recent":
                    merged_filters["year_start"] = 2023
                flt_key = saved_flt
            else:
                merged_filters = {}
                flt_key = "all"

        # Step 1: Fuzzy Auto-Correct on clean query
        correction = fuzzy_engine.process_query(clean_query)

        if correction.action == "PROMPT_USER":
            kb = get_confirmation_keyboard(correction.corrected_query, clean_query)
            await safe_reply(
                message,
                f"🤔 *Maksud Anda:*\n_{correction.corrected_query}_\n\nKeyakinan: *{int(correction.overall_confidence * 100)}%*",
                reply_markup=kb,
                parse_mode=ParseMode.MARKDOWN
            )
            return

        search_term = correction.corrected_query if correction.action == "AUTO_CORRECTED" else clean_query
        await execute_search(
            message,
            search_term,
            filters=merged_filters,
            active_filter_key=flt_key,
            correction=correction if correction.action == "AUTO_CORRECTED" else None
        )
    except Exception as e:
        logger.exception("Error processing search: %s", e)
        await safe_reply(message, f"❌ Terjadi kesalahan saat memproses pencarian: {str(e)}", parse_mode=None)

async def execute_search(
    message: types.Message,
    search_term: str,
    filters: dict | None = None,
    active_filter_key: str = "all",
    correction=None,
    edit_message: types.Message | None = None
):
    info_msg = ""
    if correction:
        info_msg = f"🔎 *Koreksi Kata Kunci:* `{correction.corrected_query}` (Akurasi: {int(correction.overall_confidence * 100)}%)\n\n"

    filter_label_map = {
        "all": "OpenAlex, Scopus, Crossref, dan SINTA",
        "scopus": "🏛️ Scopus (International Indexed)",
        "sinta": "🇮🇩 SINTA / GARUDA (National Accredited)",
        "openalex": "📖 OpenAlex (Global Open Index)",
        "oa": "🔓 Open Access (Full Text)",
        "recent": "📅 Publikasi Terbaru (>= 2023)"
    }
    src_label = filter_label_map.get(active_filter_key, "Multi-sumber")
    prompt_text = f"{info_msg}⚡ Mencari di {src_label}..."

    if edit_message:
        status_msg = edit_message
        try:
            await edit_message.edit_text(prompt_text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await edit_message.edit_text(prompt_text, parse_mode=None)
    else:
        status_msg = await safe_reply(message, prompt_text, parse_mode=ParseMode.MARKDOWN)

    try:
        # Step 2: Multi-source search with optional filters
        query_kwargs = {"raw_query": search_term, "limit": 5}
        if filters:
            if "providers" in filters:
                query_kwargs["providers"] = filters["providers"]
            if "open_access_only" in filters:
                query_kwargs["open_access_only"] = filters["open_access_only"]
            if "year_start" in filters:
                query_kwargs["year_start"] = filters["year_start"]
            if "year_end" in filters:
                query_kwargs["year_end"] = filters["year_end"]

        query_obj = SearchQuery(**query_kwargs)
        papers = await aggregator.search(query_obj)

        chat_id = message.chat.id
        USER_SEARCH_CONTEXT[chat_id] = {
            "query": search_term,
            "filter": active_filter_key,
            "filters": filters or {}
        }

        if not papers:
            not_found_text = f"{info_msg}❌ Tidak ditemukan paper ilmiah untuk `{search_term}` dengan filter *{src_label}*."
            try:
                await status_msg.edit_text(not_found_text, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await status_msg.edit_text(not_found_text, parse_mode=None)
            return

        USER_SESSIONS[chat_id] = papers
        await send_paper_result(
            message,
            papers,
            index=0,
            active_filter=active_filter_key,
            edit_message=status_msg
        )
    except Exception as e:
        logger.exception("Error executing paper search: %s", e)
        err_text = f"❌ Terjadi kesalahan saat mencari literatur: {str(e)}"
        try:
            await status_msg.edit_text(err_text, parse_mode=None)
        except Exception:
            await safe_reply(message, err_text, parse_mode=None)

async def send_paper_result(
    message: types.Message,
    papers: list[Paper],
    index: int,
    active_filter: str = "all",
    edit_message: types.Message | None = None
):
    paper = papers[index]
    authors_str = ", ".join([a.name for a in paper.authors[:3]]) if paper.authors else "Unknown"
    abstract_preview = (paper.abstract[:240] + "...") if paper.abstract else "Abstrak belum tersedia di ringkasan publik."

    # Direct links
    links = []
    if paper.doi_url:
        links.append(f"[DOI Resolver]({paper.doi_url})")
    if paper.full_text_url:
        links.append(f"[Direct PDF]({paper.full_text_url})")
    if paper.landing_page_url:
        links.append(f"[Web Portal]({paper.landing_page_url})")
    link_display = " • ".join(links) if links else "`Link publik belum terindeks`"

    filter_label_map = {
        "all": "Semua Indeks",
        "scopus": "Scopus",
        "sinta": "SINTA / GARUDA",
        "openalex": "OpenAlex",
        "oa": "Open Access",
        "recent": "Terbaru"
    }
    filter_badge = f" | 🎯 `{filter_label_map.get(active_filter, active_filter)}`" if active_filter != "all" else ""

    text = (
        f"📚 *HASIL PENCARIAN ({index + 1}/{len(papers)})*{filter_badge}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 *{paper.title}*\n"
        f"👤 *Penulis:* {authors_str}\n"
        f"📅 *Tahun:* {paper.year or 'N/A'} | 🏛️ *Sumber:* {paper.source}\n"
        f"⭐ *Relevansi:* {int(paper.composite_relevance * 100)}% | 📊 *Sitasi:* {paper.citation_count}\n\n"
        f"💡 *Reasoning Relevansi:*\n_{paper.relevance_reasoning}_\n\n"
        f"🌐 *Direct Access:* {link_display}\n\n"
        f"📝 *Abstrak:*\n_{abstract_preview}_\n"
    )

    kb = get_paper_keyboard(
        doi=paper.doi or paper.id,
        current_idx=index,
        total_count=len(papers),
        direct_url=paper.direct_url,
        pdf_url=paper.full_text_url,
        active_filter=active_filter
    )
    if edit_message:
        try:
            await edit_message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        except Exception:
            # Fallback without markdown if title/abstract has entity conflicts
            plain_link = paper.direct_url or "Belum tersedia"
            plain_badge = f" | Filter: {filter_label_map.get(active_filter, active_filter)}" if active_filter != "all" else ""
            fallback_text = (
                f"📚 HASIL PENCARIAN ({index + 1}/{len(papers)}){plain_badge}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📄 {paper.title}\n"
                f"👤 Penulis: {authors_str}\n"
                f"📅 Tahun: {paper.year or 'N/A'} | 🏛️ Sumber: {paper.source}\n"
                f"⭐ Relevansi: {int(paper.composite_relevance * 100)}% | 📊 Sitasi: {paper.citation_count}\n\n"
                f"💡 Reasoning Relevansi:\n{paper.relevance_reasoning}\n\n"
                f"🌐 Link Artikel: {plain_link}\n\n"
                f"📝 Abstrak:\n{abstract_preview}\n"
            )
            await edit_message.edit_text(fallback_text, reply_markup=kb, parse_mode=None)
    else:
        await safe_reply(message, text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

# ------------------------------------------------------------------------------
# 5. Matrix, Gap Analysis, & Brainstorming
# ------------------------------------------------------------------------------

@router.message(Command("brainstorm", "ide", "brainstorming"))
async def cmd_brainstorm(message: types.Message, state: FSMContext | None = None):
    if state:
        await state.clear()
    text = message.text or ""
    parts = text.split(maxsplit=1)
    topic = parts[1].strip() if len(parts) > 1 else ""
    if not topic:
        if state:
            await state.set_state(BotStates.waiting_for_brainstorm_topic)
        await safe_reply(
            message,
            "⚠️ Silakan masukkan topik atau ide riset yang ingin di-brainstorming.\n_Contoh:_ `/brainstorm cyber security zero trust`",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    await execute_brainstorm(message, topic)

async def execute_brainstorm(message: types.Message, topic: str, seed_papers: list[Paper] | None = None):
    status_msg = await safe_reply(message, f"💡 Melakukan AI brainstorming untuk topik *{topic}*...", parse_mode=ParseMode.MARKDOWN)

    # Search relevant papers if none provided
    papers = seed_papers
    if not papers:
        query_obj = SearchQuery(raw_query=topic, limit=3)
        try:
            papers = await aggregator.search(query_obj)
        except Exception:
            papers = []

    result = ResearchBrainstormer.generate(topic, seed_papers=papers)
    md_text = ResearchBrainstormer.to_markdown(result)

    if len(md_text) > 4000:
        md_text = md_text[:3950] + "\n\n*(Dipotong karena batas karakter Telegram)*"

    try:
        await status_msg.edit_text(md_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    except Exception:
        await status_msg.edit_text(md_text, parse_mode=None)

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
    status_msg = await safe_reply(message, f"🔍 Menganalisis research gap & peluang novelty untuk *{topic}*...", parse_mode=ParseMode.MARKDOWN)
    query_obj = SearchQuery(raw_query=topic, limit=5)
    papers = await aggregator.search(query_obj)

    if not papers:
        await status_msg.edit_text(f"❌ Tidak ditemukan paper untuk menganalisis gap `{topic}`.", parse_mode=None)
        return

    report = ResearchGapFinder.find_gaps(topic, papers)
    lines = [
        f"🔬 *ANALISIS RESEARCH GAP & PELUANG NOVELTY*\n"
        f"🎯 *Topik:* `{report.topic}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ]
    for idx, gap in enumerate(report.gaps, 1):
        lines.append(f"📌 *{idx}. [{gap.category}] {gap.title}* (Urgensi: `{gap.severity}`)")
        lines.append(f"{gap.description}")
        if gap.novelty_opportunity:
            lines.append(f"💡 _{gap.novelty_opportunity}_\n")
        else:
            lines.append("")

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
    chat_id = callback.message.chat.id
    saved_ctx = USER_SEARCH_CONTEXT.get(chat_id, {})
    flt_key = saved_ctx.get("filter", "all")
    filters = saved_ctx.get("filters", {})
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await execute_search(
        callback.message,
        corr_term,
        filters=filters,
        active_filter_key=flt_key,
        edit_message=callback.message
    )
    await callback.answer()

@router.callback_query(F.data.startswith("search_raw:"))
async def on_search_raw(callback: types.CallbackQuery):
    raw_term = callback.data.split(":", 1)[1]
    chat_id = callback.message.chat.id
    saved_ctx = USER_SEARCH_CONTEXT.get(chat_id, {})
    flt_key = saved_ctx.get("filter", "all")
    filters = saved_ctx.get("filters", {})
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await execute_search(
        callback.message,
        raw_term,
        filters=filters,
        active_filter_key=flt_key,
        edit_message=callback.message
    )
    await callback.answer()

@router.callback_query(F.data.startswith("nav_page:"))
async def on_nav_page(callback: types.CallbackQuery):
    idx = int(callback.data.split(":")[1])
    chat_id = callback.message.chat.id
    papers = USER_SESSIONS.get(chat_id, [])
    active_flt = USER_SEARCH_CONTEXT.get(chat_id, {}).get("filter", "all")
    if 0 <= idx < len(papers):
        await send_paper_result(
            callback.message,
            papers,
            index=idx,
            active_filter=active_flt,
            edit_message=callback.message
        )
    await callback.answer()

@router.callback_query(F.data == "act_flt_menu:")
async def on_filter_menu_callback(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    current_flt = USER_SEARCH_CONTEXT.get(chat_id, {}).get("filter", "all")
    kb = get_filter_selection_keyboard(active_filter=current_flt)
    await safe_reply(
        callback.message,
        "🎯 *Filter Indeks & Kategori Riset*\n\n"
        "Pilih indeks publikasi atau kategori untuk memfilter hasil pencarian:\n"
        "• 🏛️ *Scopus*: Jurnal & prosiding internasional terindeks Scopus\n"
        "• 🇮🇩 *SINTA / GARUDA*: Jurnal nasional terakreditasi Kemdikbudristek\n"
        "• 📖 *OpenAlex*: Basis data bibliometrik global terbuka\n"
        "• 🔓 *Open Access*: Artikel gratis dapat diunduh (PDF langsung)\n"
        "• 📅 *Terbaru*: Khusus publikasi mutakhir (>= 2023)\n\n"
        f"Status aktif: *{current_flt.upper()}*",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.callback_query(F.data.startswith("flt_set:"))
async def on_filter_set_callback(callback: types.CallbackQuery):
    key = callback.data.split(":")[1]
    chat_id = callback.message.chat.id
    if chat_id not in USER_SEARCH_CONTEXT:
        USER_SEARCH_CONTEXT[chat_id] = {}
    USER_SEARCH_CONTEXT[chat_id]["filter"] = key

    filter_label_map = {
        "all": "🌐 Semua Indeks",
        "scopus": "🏛️ Scopus",
        "sinta": "🇮🇩 SINTA / GARUDA",
        "openalex": "📖 OpenAlex",
        "oa": "🔓 Open Access",
        "recent": "📅 Terbaru (>=2023)"
    }
    label = filter_label_map.get(key, key)

    extra_filters = {}
    if key in ["scopus", "sinta", "openalex"]:
        extra_filters["providers"] = [key]
    elif key == "oa":
        extra_filters["open_access_only"] = True
    elif key == "recent":
        extra_filters["year_start"] = 2023
    USER_SEARCH_CONTEXT[chat_id]["filters"] = extra_filters

    current_query = USER_SEARCH_CONTEXT[chat_id].get("query")
    if current_query:
        await callback.answer(f"Menerapkan filter: {label}")
        await execute_search(
            callback.message,
            current_query,
            filters=extra_filters,
            active_filter_key=key,
            edit_message=callback.message
        )
    else:
        await callback.answer(f"Filter diset: {label}")
        await safe_reply(
            callback.message,
            f"✅ Filter aktif diset ke: *{label}*\n\nSilakan ketik topik riset yang ingin Anda cari:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

@router.callback_query(F.data == "flt_close:search")
async def on_filter_close_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_for_search_query)
    chat_id = callback.message.chat.id
    current_flt = USER_SEARCH_CONTEXT.get(chat_id, {}).get("filter", "all")
    await safe_reply(
        callback.message,
        f"🔍 *Siap mencari paper!*\nFilter aktif saat ini: *{current_flt.upper()}*\n\nSilakan ketik kata kunci atau topik riset Anda:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
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
        direct_link = target.direct_url or "Link publik belum terindeks"
        text = (
            f"🔬 *Analisis Mendalam Paper:*\n*{analysis.title}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Tujuan Riset:* {analysis.research_objective}\n"
            f"🛠️ *Metodologi:* {', '.join(analysis.algorithms_used)}\n"
            f"📊 *Dataset:* {analysis.dataset}\n"
            f"📈 *Temuan Utama:* {analysis.key_findings}\n"
            f"⚠️ *Limitasi:* {analysis.limitations}\n\n"
            f"🧠 *Scientific Reasoning:*\n_{analysis.reasoning or 'Model terbukti efektif pada domain yang dievaluasi.'}_\n\n"
            f"🌐 *Direct Link:* {direct_link}"
        )
        await safe_reply(callback.message, text, parse_mode=ParseMode.MARKDOWN)
    await callback.answer("Analisis selesai!")

@router.callback_query(F.data.startswith("act_brain:"))
async def on_brainstorm_callback(callback: types.CallbackQuery):
    doi = callback.data.split(":")[1]
    papers = USER_SESSIONS.get(callback.message.chat.id, [])
    target = next((p for p in papers if p.doi == doi or p.id == doi), papers[0] if papers else None)
    if target:
        await callback.answer("Menyiapkan ide riset...")
        topic = target.title
        await execute_brainstorm(callback.message, topic, seed_papers=[target])
    else:
        await callback.answer("Paper tidak ditemukan di sesi ini.", show_alert=True)

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
