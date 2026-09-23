import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from literax.config import settings
from literax.bot.handlers import router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("literax.bot")

async def run_bot() -> None:
    if not settings.bot_token:
        logger.error("❌ BOT_TOKEN is not configured in .env! Bot cannot start.")
        logger.info("👉 Get a token from @BotFather on Telegram and set BOT_TOKEN in .env")
        return

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        me = await bot.get_me()
        logger.info("==================================================")
        logger.info("🤖 LiteraX Bot Connected: @%s (ID: %s)", me.username, me.id)
        logger.info("📛 Display Name: %s", me.first_name)
        logger.info("==================================================")

        # Clear any existing webhook before starting long polling
        await bot.delete_webhook(drop_pending_updates=False)

        # Register bot commands for the Telegram Menu button
        commands = [
            BotCommand(command="cari", description="🔍 Cari paper ilmiah & literatur"),
            BotCommand(command="search", description="🔍 Search academic literature"),
            BotCommand(command="scopus", description="🏛️ Cari khusus publikasi Scopus"),
            BotCommand(command="sinta", description="🇮🇩 Cari khusus jurnal SINTA / GARUDA"),
            BotCommand(command="priority", description="⭐ Pilih rekomendasi Scopus/SINTA dulu"),
            BotCommand(command="filter", description="🎯 Atur filter indeks & kategori"),
            BotCommand(command="brainstorm", description="💡 Brainstorm ide riset & novelty"),
            BotCommand(command="saved", description="📚 Koleksi paper tersimpan"),
            BotCommand(command="matrix", description="📊 Buat literature review matrix"),
            BotCommand(command="gap", description="🔬 Analisis research gap"),
            BotCommand(command="cite", description="📖 Format sitasi (APA, BibTeX)"),
            BotCommand(command="help", description="❓ Panduan & bantuan bot"),
        ]
        await bot.set_my_commands(commands)
        logger.info("📋 Bot commands menu registered successfully.")

        logger.info("🚀 LiteraX Telegram Bot is LIVE and polling updates...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("💥 Fatal error during Telegram bot execution: %s", e)
    finally:
        await bot.session.close()
        logger.info("🛑 LiteraX Telegram Bot session closed gracefully.")

def main():
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Bot stopped by user signal.")

if __name__ == "__main__":
    main()
