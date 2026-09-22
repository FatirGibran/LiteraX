import pytest
from aiogram import Router
from literax.bot.handlers import router, USER_SESSIONS, WELCOME_MESSAGE_TEXT
from literax.bot.keyboards import get_confirmation_keyboard, get_paper_keyboard
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
    conf_kb = get_confirmation_keyboard("machine learning", "machin lerning")
    assert conf_kb is not None
    assert len(conf_kb.inline_keyboard) > 0

    paper_kb = get_paper_keyboard("10.1016/j.cose.2024.103982", 0, 5)
    assert paper_kb is not None
    assert len(paper_kb.inline_keyboard) > 0

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
