"""Regression: Telegram's error description must survive HTTP error handling."""
import json

import pytest
import requests

from conftest import FakeResponse
from tools.send.tool import send_telegram


@pytest.fixture
def telegram_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:private-test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001234567890")


def test_telegram_400_preserves_chat_not_found_description(telegram_env, fake_http):
    calls = fake_http(FakeResponse({
        "ok": False, "error_code": 400, "description": "Bad Request: chat not found",
    }, status_code=400))
    result = send_telegram("Hello", confirmed=True)
    assert result["error"] == "HTTPError"
    assert result["message"] == "Bad Request: chat not found"
    assert result["status_code"] == 400
    assert len(calls) == 1  # An action error must not trigger an automatic retry.


def test_telegram_non_json_error_has_safe_http_status(telegram_env, fake_http):
    class NonJsonResponse(FakeResponse):
        def json(self):
            raise ValueError("HTML response")

    fake_http(NonJsonResponse(status_code=502))
    result = send_telegram("Hello", confirmed=True)
    assert result["error"] == "HTTPError"
    assert result["status_code"] == 502
    assert "502" in result["message"]


def test_telegram_transport_error_does_not_expose_token(telegram_env, fake_http):
    calls = fake_http(requests.ConnectionError(
        "Failed to connect to https://api.telegram.org/bot123456:private-test-token/sendMessage",
    ))
    result = send_telegram("Hello", confirmed=True)
    assert result["error"] == "ConnectionError"
    assert "123456:private-test-token" not in json.dumps(result)
    assert len(calls) == 1


def test_telegram_confirmed_success_keeps_existing_payload(telegram_env, fake_http):
    calls = fake_http(FakeResponse({"ok": True, "result": {"message_id": 1}}))
    assert send_telegram("Hello", confirmed=True)["status"] == "sent"
    assert calls[0]["json"] == {
        "chat_id": "-1001234567890", "text": "Hello", "parse_mode": "Markdown",
    }
