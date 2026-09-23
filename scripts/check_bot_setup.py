#!/usr/bin/env python3
"""
LiteraX Diagnostics & Health Check Script
Verifies environment variables, Telegram Bot connectivity, and Web Server status.
"""

import asyncio
import sys
import httpx
from literax.config import settings

async def main():
    print("=" * 60)
    print("🔬 LiteraX Diagnostics: Telegram Bot & Server Connection Check")
    print("=" * 60)

    # 1. Check Configuration
    print("\n[1] Checking Configuration (.env)...")
    if not settings.bot_token:
        print("  ❌ BOT_TOKEN is NOT set!")
        print("  👉 Create a bot via @BotFather on Telegram and set BOT_TOKEN in .env")
        bot_configured = False
    else:
        # Mask token for security
        masked = settings.bot_token[:6] + "..." + settings.bot_token[-4:]
        print(f"  ✅ BOT_TOKEN found: {masked}")
        bot_configured = True

    print(f"  ℹ️  Telegram Mode: {settings.telegram_mode}")
    if settings.telegram_mode == "webhook":
        print(f"  ℹ️  Webhook URL: {settings.telegram_webhook_url or 'NOT SET'}")

    # 2. Check Telegram API Connectivity
    if bot_configured:
        print("\n[2] Connecting to Telegram API (api.telegram.org)...")
        try:
            from aiogram import Bot
            bot = Bot(token=settings.bot_token)
            me = await bot.get_me()
            print("  ✅ Successfully connected to Telegram!")
            print(f"  🤖 Bot Username: @{me.username}")
            print(f"  📛 Display Name: {me.first_name}")
            print(f"  🆔 Bot ID: {me.id}")
            print(f"  👥 Can join groups: {me.can_join_groups}")

            webhook_info = await bot.get_webhook_info()
            print(f"  📡 Current Telegram Webhook URL: {webhook_info.url or 'None (Polling Mode Active)'}")
            if webhook_info.pending_update_count > 0:
                print(f"  📬 Pending updates on Telegram: {webhook_info.pending_update_count}")
            await bot.session.close()
        except Exception as e:
            print(f"  ❌ Failed to connect to Telegram: {e}")

    # 3. Check Local Web Server (FastAPI)
    print("\n[3] Checking Web Server (FastAPI Gateway)...")
    url = f"http://127.0.0.1:{settings.app_port}/health"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                print(f"  ✅ Web Server is running on port {settings.app_port}!")
                print(f"  📄 Status: {resp.json()}")
            else:
                print(f"  ⚠️  Web Server returned status code {resp.status_code}")
    except httpx.ConnectError:
        print(f"  ℹ️  Web Server is not running on http://127.0.0.1:{settings.app_port}.")
        print("  💡 Start it with: uvicorn literax.api.main:app --host 0.0.0.0 --port 8000")

    print("\n" + "=" * 60)
    print("🏁 Diagnostics completed.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
