from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from literax.api.routes import router
from literax.config import settings

logger = logging.getLogger("literax.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: register webhook if configured
    if settings.bot_token and settings.telegram_mode == "webhook" and settings.telegram_webhook_url:
        try:
            from literax.api.routes import get_telegram_instances
            bot, _ = get_telegram_instances()
            if bot:
                await bot.set_webhook(
                    url=settings.telegram_webhook_url,
                    secret_token=settings.telegram_webhook_secret,
                    drop_pending_updates=False
                )
                me = await bot.get_me()
                logger.info("🤖 Telegram Webhook active for @%s at %s", me.username, settings.telegram_webhook_url)
        except Exception as e:
            logger.warning("⚠️ Could not auto-register Telegram webhook on startup: %s", e)

    yield

    # Shutdown: gracefully close bot session
    from literax.api.routes import _bot_instance
    if _bot_instance:
        try:
            await _bot_instance.session.close()
            logger.info("🛑 Webhook bot session closed gracefully.")
        except Exception:
            pass

app = FastAPI(
    title="LiteraX API",
    description="AI-Powered Academic Research Assistant & Multi-Source Engine",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "LiteraX API Gateway",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)
