import asyncio
import logging
from aiogram import Bot, Dispatcher
from literax.config import settings
from literax.bot.handlers import router

logging.basicConfig(level=logging.INFO)

async def main():
    if not settings.bot_token:
        logging.warning("⚠️ BOT_TOKEN is not set in .env. Bot polling cannot start.")
        return

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    logging.info("🚀 LiteraX Telegram Bot started polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
