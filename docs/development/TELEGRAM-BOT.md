# 🤖 Telegram Bot Architecture & User Guide

LiteraX features an asynchronous Telegram bot powered by **aiogram 3.x**. It serves as an accessible interface for researchers on desktop and mobile.

---

## 📋 Bot Commands Reference

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| `/start` | None | Initializes bot session, displays welcome instructions & refreshes menu | `/start` |
| `/search` | `<query>` | Executes fuzzy auto-corrected multi-source search | `/search machne lerning phising` |
| `/scopus` | `<query>` | Targeted search exclusively in Elsevier Scopus index | `/scopus zero trust network` |
| `/sinta` | `<query>` | Targeted search in Indonesian SINTA / GARUDA accredited journals | `/sinta sistem pendukung keputusan` |
| `/priority` / `/urutan` | None | Sets recommendation priority (Scopus first, SINTA first, best relevance) | `/priority` |
| `/filter` | None | Opens interactive index & category selection keyboard | `/filter` |
| `/brainstorm`| `[topic]` | AI research ideation, problem statements, and novelty | `/brainstorm federated learning` |
| `/analyze` | `<doi>` | Generates structured AI decomposition of a paper | `/analyze 10.1016/j.cose.2024.103982` |
| `/matrix` | `[topic]` | Compiles a comparative literature review matrix | `/matrix phishing detection` |
| `/gap` | `[topic]` | Synthesizes potential research gaps from literature | `/gap phishing detection` |
| `/cite` | `<doi>` | Generates citations in APA, IEEE, Harvard, BibTeX | `/cite 10.1016/j.cose.2024.103982` |
| `/save` | `<doi>` | Saves paper to user's active research session | `/save 10.1016/j.cose.2024.103982` |
| `/saved` | `[export fmt]` | Lists all saved papers (exportable as markdown/csv/bibtex) | `/saved export csv` |
| `/clear` | None | Clears current research session | `/clear` |

### 🎯 Recommendation Priority & Search Filter Syntax Prefixes
Users can set recommendation priorities and filter searches directly:
- **Prioritas Rekomendasi (Recommends Specific Index First across all sources)**:
  - `scopus dulu: <topic>` or `scopus first: <topic>` — Displays Scopus papers first, followed by others
  - `sinta dulu: <topic>` or `sinta first: <topic>` — Displays SINTA / GARUDA papers first, followed by others
  - `priority:scopus <topic>` or `priority:sinta <topic>` — Explicit priority prefix
- **Filter Eksklusif (Only returns matching sources)**:
  - `scopus: <topic>` — Filter exclusively to Scopus indexed publications
  - `sinta: <topic>` or `garuda: <topic>` — Filter exclusively to SINTA / GARUDA Indonesian journals
  - `oa: <topic>` or `openaccess: <topic>` — Filter to Open Access articles with direct PDF
  - `year:YYYY <topic>` — Filter to publications from a specific year onwards (e.g. `year:2024 AI ethics`)

---

## 🎨 Interactive User Workflow

### 1. Typo Handling & Disambiguation
When a query yields medium confidence ($0.70 \le C < 0.90$):

```text
LiteraX Bot:
🤔 Did you mean: "cyber security for phishing"?
Confidence: 82%

[✅ Yes, Search This]  [❌ Keep Original]
```

### 2. Search Result Card & Inline Controls
Each paper hit is rendered with interactive inline buttons:

```text
📚 Paper 1/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title: Machine Learning Approaches for Phishing URL Detection
Year: 2025 | Source: Scopus | Citations: 34
Relevance: 96%

[📄 View Abstract]  [🔬 Deep AI Analysis]
[📖 Get Citation]   [💾 Save to Session]
[⬅️ Previous]       [➡️ Next Paper]
```

---

## 💻 aiogram Handler Architecture

LiteraX structures bot handlers using `aiogram.Router`:

```python
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

search_router = Router()

@search_router.message(Command("search"))
async def handle_search_command(message: types.Message):
    raw_query = message.text.replace("/search", "").strip()
    if not raw_query:
        await message.reply("⚠️ Please provide a search query. Example:\n`/search machine learning phishing`")
        return

    # Notify typing action
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # 1. Fuzzy Logic Auto-Correct
    correction = await fuzzy_engine.process(raw_query)
    
    if correction.action == "PROMPT_USER":
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Yes", callback_data=f"confirm_{correction.corrected}")
        builder.button(text="❌ Keep Original", callback_data=f"raw_{raw_query}")
        await message.reply(
            f"🤔 Did you mean: *{correction.corrected}*? (Confidence: {int(correction.confidence*100)}%)",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        return

    # 2. Multi-source Search
    papers = await aggregator.search_all(correction.corrected)
    # Render first paper with pagination
    await send_paper_card(message, papers, index=0)
```

---

## ⚙️ Session State Management (Redis FSM)

The bot tracks user state and paginated card indices using `RedisStorage`:

```python
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

redis_client = Redis.from_url("redis://localhost:6379/0")
storage = RedisStorage(redis=redis_client)
```

This ensures that restarting the bot server does not disrupt active user dialogues or pagination states.
