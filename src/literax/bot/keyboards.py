from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_confirmation_keyboard(corrected_query: str, raw_query: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yes, Search This", callback_data=f"search_corr:{corrected_query[:40]}")
    builder.button(text="❌ Keep Original", callback_data=f"search_raw:{raw_query[:40]}")
    builder.adjust(2)
    return builder.as_markup()

def get_paper_keyboard(doi: str | None, current_idx: int, total_count: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Action buttons
    clean_doi = (doi or "none")[:30]
    builder.button(text="🔬 Analyze", callback_data=f"act_ana:{clean_doi}")
    builder.button(text="📖 Cite", callback_data=f"act_cite:{clean_doi}")
    builder.button(text="💾 Save", callback_data=f"act_save:{clean_doi}")

    # Navigation buttons
    nav_buttons = []
    if current_idx > 0:
        builder.button(text="⬅️ Prev", callback_data=f"nav_page:{current_idx-1}")
    if current_idx < total_count - 1:
        builder.button(text="Next ➡️", callback_data=f"nav_page:{current_idx+1}")

    builder.adjust(3, 2)
    return builder.as_markup()

def get_export_format_keyboard() -> InlineKeyboardMarkup:
    """Generates inline keyboard for selecting collection export format."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Markdown", callback_data="exp_fmt:markdown")
    builder.button(text="📊 CSV", callback_data="exp_fmt:csv")
    builder.button(text="📚 BibTeX", callback_data="exp_fmt:bibtex")
    builder.adjust(3)
    return builder.as_markup()
