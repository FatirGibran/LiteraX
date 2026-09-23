import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from starlette.testclient import TestClient
from literax.api.main import app
from literax.config import settings

client = TestClient(app)

def test_telegram_status_unconfigured():
    with patch.object(settings, "bot_token", None):
        response = client.get("/api/v1/telegram/status")
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is False
        assert "BOT_TOKEN is not configured" in data["status"]

def test_telegram_webhook_unconfigured():
    with patch.object(settings, "bot_token", None):
        response = client.post("/api/v1/telegram/webhook", json={"update_id": 123})
        assert response.status_code == 503

def test_telegram_set_webhook_unconfigured():
    with patch.object(settings, "bot_token", None):
        response = client.post("/api/v1/telegram/set-webhook")
        assert response.status_code == 503

def test_telegram_delete_webhook_unconfigured():
    with patch.object(settings, "bot_token", None):
        response = client.post("/api/v1/telegram/delete-webhook")
        assert response.status_code == 503

def test_telegram_webhook_secret_validation():
    with patch.object(settings, "bot_token", "12345:fake_token"), \
         patch.object(settings, "telegram_webhook_secret", "my_secret_token"):
        
        # Wrong secret token
        response = client.post(
            "/api/v1/telegram/webhook",
            json={"update_id": 1},
            headers={"x-telegram-bot-api-secret-token": "wrong_token"}
        )
        assert response.status_code == 403
