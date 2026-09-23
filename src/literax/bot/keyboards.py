from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Returns persistent reply keyboard menu shown at the bottom of the chat."""
    kb = [
        [
            KeyboardButton(text="🔍 Cari Paper"),
            KeyboardButton(text="💡 Brainstorm Ide Riset")
        ],
        [
            KeyboardButton(text="📊 Literature Matrix"),
            KeyboardButton(text="🔬 Research Gap")
        ],
        [
            KeyboardButton(text="📚 Paper Tersimpan"),
            KeyboardButton(text="❓ Panduan & Bantuan")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Pilih menu atau ketik topik riset..."
    )

def get_confirmation_keyboard(corrected_query: str, raw_query: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yes, Search This", callback_data=f"search_corr:{corrected_query[:40]}")
    builder.button(text="❌ Keep Original", callback_data=f"search_raw:{raw_query[:40]}")
    builder.adjust(2)
    return builder.as_markup()

def get_paper_keyboard(
    doi: str | None,
    current_idx: int,
    total_count: int,
    direct_url: str | None = None,
    pdf_url: str | None = None,
    active_filter: str = "all"
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Direct access URL buttons
    link_buttons_count = 0
    if direct_url and direct_url.startswith("http"):
        builder.button(text="🔗 Buka Artikel", url=direct_url)
        link_buttons_count += 1
    if pdf_url and pdf_url.startswith("http") and pdf_url != direct_url:
        builder.button(text="📥 Direct PDF", url=pdf_url)
        link_buttons_count += 1

    # Action buttons
    clean_doi = (doi or "none")[:30]
    builder.button(text="🔬 Analisis", callback_data=f"act_ana:{clean_doi}")
    builder.button(text="📖 Sitasi", callback_data=f"act_cite:{clean_doi}")
    builder.button(text="💡 Brainstorm", callback_data=f"act_brain:{clean_doi}")
    builder.button(text="💾 Simpan", callback_data=f"act_save:{clean_doi}")

    # Navigation buttons
    nav_buttons_count = 0
    if current_idx > 0:
        builder.button(text="⬅️ Prev", callback_data=f"nav_page:{current_idx-1}")
        nav_buttons_count += 1
    if current_idx < total_count - 1:
        builder.button(text="Next ➡️", callback_data=f"nav_page:{current_idx+1}")
        nav_buttons_count += 1

    # Filter toggle button
    filter_label_map = {
        "all": "🌐 Semua",
        "scopus": "🏛️ Scopus",
        "sinta": "🇮🇩 SINTA",
        "openalex": "📖 OpenAlex",
        "oa": "🔓 OpenAccess",
        "recent": "📅 Terbaru"
    }
    cur_label = filter_label_map.get(active_filter, "🌐 Filter")
    builder.button(text=f"🎯 Filter Indeks: {cur_label}", callback_data="act_flt_menu:")

    sizes = []
    if link_buttons_count > 0:
        sizes.append(link_buttons_count)
    sizes.append(4)
    if nav_buttons_count > 0:
        sizes.append(nav_buttons_count)
    sizes.append(1)

    builder.adjust(*sizes)
    return builder.as_markup()

def get_filter_selection_keyboard(active_filter: str = "all") -> InlineKeyboardMarkup:
    """Generates inline keyboard for filtering searches by index/category."""
    builder = InlineKeyboardBuilder()

    filters = [
        ("all", "🌐 Semua Indeks"),
        ("scopus", "🏛️ Scopus"),
        ("sinta", "🇮🇩 SINTA / GARUDA"),
        ("openalex", "📖 OpenAlex"),
        ("oa", "🔓 Open Access"),
        ("recent", "📅 Terbaru (>=2023)"),
    ]

    for key, label in filters:
        indicator = " ✅" if key == active_filter else ""
        builder.button(text=f"{label}{indicator}", callback_data=f"flt_set:{key}")

    builder.button(text="🔍 Mulai Cari Topik", callback_data="flt_close:search")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_export_format_keyboard() -> InlineKeyboardMarkup:
    """Generates inline keyboard for selecting collection export format."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Markdown", callback_data="exp_fmt:markdown")
    builder.button(text="📊 CSV", callback_data="exp_fmt:csv")
    builder.button(text="📚 BibTeX", callback_data="exp_fmt:bibtex")
    builder.adjust(3)
    return builder.as_markup()
