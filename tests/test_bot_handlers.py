import pytest
from aiogram import Router
from literax.bot.handlers import router, USER_SESSIONS, WELCOME_MESSAGE_TEXT
from literax.bot.keyboards import (
    get_confirmation_keyboard,
    get_paper_keyboard,
    get_export_format_keyboard,
    get_main_menu_keyboard
)
from literax.models import Paper, Author
from literax.storage.collection import default_collection_manager

def test_bot_welcome_text_constant():
    assert "🔬 *Welcome to LiteraX" in WELCOME_MESSAGE_TEXT
    assert "/search" in WELCOME_MESSAGE_TEXT
    assert "/matrix" in WELCOME_MESSAGE_TEXT
    assert "/cite" in WELCOME_MESSAGE_TEXT

def test_bot_router_registration():
    assert isinstance(router, Router)
    # Check that message and callback handlers are registered
    assert len(router.message.handlers) >= 6
    assert len(router.callback_query.handlers) >= 5

def test_bot_keyboards():
    main_kb = get_main_menu_keyboard()
    assert main_kb is not None
    assert len(main_kb.keyboard) >= 4
    all_buttons = [btn.text for row in main_kb.keyboard for btn in row]
    assert "🔍 Cari Paper" in all_buttons
    assert "💡 Brainstorm Riset" in all_buttons
    assert "🏛️ Rekomendasi Scopus Dulu" in all_buttons
    assert "🇮🇩 Rekomendasi SINTA Dulu" in all_buttons
    assert "🎯 Prioritas & Filter" in all_buttons

    conf_kb = get_confirmation_keyboard("machine learning", "machin lerning")
    assert conf_kb is not None
    assert len(conf_kb.inline_keyboard) > 0

    paper_kb = get_paper_keyboard(
        doi="10.1016/j.cose.2024.103982",
        current_idx=0,
        total_count=5,
        direct_url="https://doi.org/10.1016/j.cose.2024.103982",
        pdf_url="https://example.com/paper.pdf"
    )
    assert paper_kb is not None
    assert len(paper_kb.inline_keyboard) >= 2
    # Verify direct url button exists
    assert any(btn.url == "https://doi.org/10.1016/j.cose.2024.103982" for row in paper_kb.inline_keyboard for btn in row)
    # Verify brainstorm action callback exists
    assert any("act_brain:" in (btn.callback_data or "") for row in paper_kb.inline_keyboard for btn in row)

    export_kb = get_export_format_keyboard()
    assert export_kb is not None
    assert len(export_kb.inline_keyboard[0]) == 3

def test_user_session_and_collection_saving():
    chat_id = 987654321
    sample_paper = Paper(
        id="bot_paper_1",
        title="AI Bot Security Review",
        doi="10.1145/bot.sec.2024",
        year=2024,
        authors=[Author(name="Researcher One")],
        journal="AI Bot Journal",
        source="Crossref"
    )

    # Put into session
    USER_SESSIONS[chat_id] = [sample_paper]
    assert len(USER_SESSIONS[chat_id]) == 1

    # Simulate saving
    added = default_collection_manager.add_paper(str(chat_id), sample_paper)
    assert added is True
    assert default_collection_manager.count(str(chat_id)) >= 1

    # Clean up
    default_collection_manager.clear_collection(str(chat_id))
    assert default_collection_manager.count(str(chat_id)) == 0

@pytest.mark.asyncio
async def test_safe_reply_helper():
    from unittest.mock import AsyncMock, MagicMock
    from literax.bot.handlers import safe_reply

    mock_msg = MagicMock()
    mock_msg.reply = AsyncMock(return_value=True)

    res = await safe_reply(mock_msg, "*Test message*")
    assert res is True
    assert mock_msg.reply.call_count == 1

def test_filter_keyboards():
    from literax.bot.keyboards import get_filter_selection_keyboard

    # Test default filter keyboard
    flt_kb = get_filter_selection_keyboard(active_priority="all", active_filter="all")
    assert flt_kb is not None
    button_callbacks = [btn.callback_data for row in flt_kb.inline_keyboard for btn in row if btn.callback_data]
    assert "flt_set:prio_scopus" in button_callbacks
    assert "flt_set:prio_sinta" in button_callbacks
    assert "flt_set:prio_openalex" in button_callbacks
    assert "flt_set:prio_all" in button_callbacks
    assert "flt_set:scopus" in button_callbacks
    assert "flt_set:sinta" in button_callbacks
    assert "flt_set:oa" in button_callbacks
    assert "flt_set:recent" in button_callbacks
    assert "flt_set:all" in button_callbacks
    assert "flt_close:search" in button_callbacks

    # Test scopus priority active indicator
    scopus_kb = get_filter_selection_keyboard(active_priority="scopus")
    scopus_btn = next(btn for row in scopus_kb.inline_keyboard for btn in row if btn.callback_data == "flt_set:prio_scopus")
    assert "✅" in scopus_btn.text

    # Test get_paper_keyboard with active priority
    paper_kb = get_paper_keyboard(
        doi="10.1016/j.cose.2024.103982",
        current_idx=0,
        total_count=3,
        active_priority="scopus"
    )
    filter_btn = next(btn for row in paper_kb.inline_keyboard for btn in row if btn.callback_data == "act_flt_menu:")
    assert "Scopus Dulu" in filter_btn.text

@pytest.mark.asyncio
async def test_filter_commands_and_sessions():
    from unittest.mock import AsyncMock, MagicMock, patch
    from literax.bot.handlers import (
        cmd_filter,
        cmd_scopus,
        cmd_sinta,
        USER_SEARCH_CONTEXT
    )

    # 1. Test /filter command
    mock_msg = MagicMock()
    mock_msg.chat.id = 12345
    mock_msg.text = "/filter"
    mock_msg.reply = AsyncMock(return_value=True)

    await cmd_filter(mock_msg)
    assert mock_msg.reply.call_count == 1
    call_args = mock_msg.reply.call_args[0][0]
    assert "Prioritas" in call_args or "Filter Indeks" in call_args

    # 2. Test /scopus without args (sets pending state)
    mock_msg_scopus = MagicMock()
    mock_msg_scopus.chat.id = 12345
    mock_msg_scopus.text = "/scopus"
    mock_msg_scopus.reply = AsyncMock(return_value=True)
    mock_state = MagicMock()
    mock_state.clear = AsyncMock()
    mock_state.set_state = AsyncMock()

    await cmd_scopus(mock_msg_scopus, state=mock_state)
    assert USER_SEARCH_CONTEXT[12345]["filter"] == "scopus"
    assert mock_msg_scopus.reply.call_count == 1

    # 3. Test /sinta with query
    with patch("literax.bot.handlers.aggregator.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [
            Paper(
                id="sinta_test_1",
                title="Sistem Pendukung Keputusan",
                year=2024,
                source="GARUDA / SINTA"
            )
        ]
        mock_msg_sinta = MagicMock()
        mock_msg_sinta.chat.id = 54321
        mock_msg_sinta.text = "/sinta sistem pendukung keputusan"
        mock_msg_sinta.reply = AsyncMock(return_value=True)

        await cmd_sinta(mock_msg_sinta)
        assert mock_search.call_count == 1
        query_arg = mock_search.call_args[0][0]
        assert query_arg.providers == ["sinta"]
        assert USER_SEARCH_CONTEXT[54321]["filter"] == "sinta"

@pytest.mark.asyncio
async def test_filter_callbacks():
    from unittest.mock import AsyncMock, MagicMock, patch
    from literax.bot.handlers import (
        on_filter_menu_callback,
        on_filter_set_callback,
        on_filter_close_callback,
        USER_SEARCH_CONTEXT
    )

    # 1. Test act_flt_menu:
    mock_cb = MagicMock()
    mock_cb.data = "act_flt_menu:"
    mock_cb.message.chat.id = 77777
    mock_cb.message.reply = AsyncMock(return_value=True)
    mock_cb.answer = AsyncMock()

    await on_filter_menu_callback(mock_cb)
    assert mock_cb.message.reply.call_count == 1
    assert mock_cb.answer.call_count == 1

    # 2. Test flt_set:prio_scopus without active query
    USER_SEARCH_CONTEXT.pop(77777, None)
    mock_set_cb = MagicMock()
    mock_set_cb.data = "flt_set:prio_scopus"
    mock_set_cb.message.chat.id = 77777
    mock_set_cb.message.reply = AsyncMock(return_value=True)
    mock_set_cb.answer = AsyncMock()

    await on_filter_set_callback(mock_set_cb)
    assert USER_SEARCH_CONTEXT[77777]["priority"] == "scopus"
    assert mock_set_cb.answer.call_count == 1

    # 3. Test flt_set:prio_sinta with active query re-executes search with priority="sinta"
    USER_SEARCH_CONTEXT[77777]["query"] = "machine learning"
    with patch("literax.bot.handlers.aggregator.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []
        mock_set_active_cb = MagicMock()
        mock_set_active_cb.data = "flt_set:prio_sinta"
        mock_set_active_cb.message.chat.id = 77777
        mock_set_active_cb.message.edit_text = AsyncMock()
        mock_set_active_cb.answer = AsyncMock()

        await on_filter_set_callback(mock_set_active_cb)
        assert mock_search.call_count == 1
        query_arg = mock_search.call_args[0][0]
        assert query_arg.priority == "sinta"

    # 4. Test flt_close:search
    mock_close_cb = MagicMock()
    mock_close_cb.data = "flt_close:search"
    mock_close_cb.message.chat.id = 77777
    mock_close_cb.message.reply = AsyncMock(return_value=True)
    mock_close_cb.answer = AsyncMock()
    mock_state = MagicMock()
    mock_state.set_state = AsyncMock()

    await on_filter_close_callback(mock_close_cb, state=mock_state)
    assert mock_close_cb.answer.call_count == 1
    assert mock_close_cb.message.reply.call_count == 1

@pytest.mark.asyncio
async def test_menu_button_handlers():
    from unittest.mock import AsyncMock, MagicMock
    from literax.bot.handlers import (
        on_menu_scopus,
        on_menu_sinta,
        on_menu_filter,
        USER_SEARCH_CONTEXT
    )

    mock_state = MagicMock()
    mock_state.set_state = AsyncMock()

    # 1. Test clicking 'Rekomendasi Scopus Dulu' menu button
    USER_SEARCH_CONTEXT.pop(99911, None)
    mock_msg_scopus = MagicMock()
    mock_msg_scopus.chat.id = 99911
    mock_msg_scopus.reply = AsyncMock(return_value=True)

    await on_menu_scopus(mock_msg_scopus, state=mock_state)
    assert USER_SEARCH_CONTEXT[99911]["priority"] == "scopus"
    assert mock_state.set_state.call_count == 1
    assert mock_msg_scopus.reply.call_count == 1
    assert "Scopus" in mock_msg_scopus.reply.call_args[0][0]

    # 2. Test clicking 'Rekomendasi SINTA Dulu' menu button
    USER_SEARCH_CONTEXT.pop(99922, None)
    mock_msg_sinta = MagicMock()
    mock_msg_sinta.chat.id = 99922
    mock_msg_sinta.reply = AsyncMock(return_value=True)

    await on_menu_sinta(mock_msg_sinta, state=mock_state)
    assert USER_SEARCH_CONTEXT[99922]["priority"] == "sinta"
    assert "SINTA / GARUDA" in mock_msg_sinta.reply.call_args[0][0]

    # 3. Test clicking 'Prioritas & Filter' menu button
    mock_msg_flt = MagicMock()
    mock_msg_flt.chat.id = 99933
    mock_msg_flt.reply = AsyncMock(return_value=True)

    await on_menu_filter(mock_msg_flt)
    assert mock_msg_flt.reply.call_count == 1
    assert "Rekomendasi & Filter" in mock_msg_flt.reply.call_args[0][0]

