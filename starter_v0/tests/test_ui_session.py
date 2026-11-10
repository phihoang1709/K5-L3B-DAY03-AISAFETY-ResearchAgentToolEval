from __future__ import annotations

import json
from pathlib import Path

import pytest

import chat
from providers.base import ModelResponse, ToolCall


class ScriptedProvider:
    default_model = "offline-model"

    def __init__(self, *responses):
        self.responses = iter(responses)
        self.messages = []

    def complete(self, messages, tools=None, **kwargs):
        self.messages.append(list(messages))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def session(tmp_path, provider):
    from ui_session import ChatSession, UISettings

    return ChatSession(UISettings(transcripts_dir=tmp_path), provider=provider)


def test_loop_supports_ui_executor_and_pauses_before_following_tools():
    executed = []

    def intercept(call):
        executed.append(call.name)
        return {"tool": call.name, "args": call.args,
                "result": {"requires_confirmation": True, "question": "Confirm?"}}

    provider = ScriptedProvider(ModelResponse(tool_calls=[
        ToolCall("send", {"text": "draft", "confirmed": True}),
        ToolCall("lookup", {"query": "must not execute"}),
    ]))
    result = chat.run_model_tool_loop(
        provider=provider, messages=[], tools=[], model=None, max_tool_rounds=4,
        tool_executor=intercept,
    )
    assert result["status"] == "waiting_for_confirmation"
    assert executed == ["send"]


def test_clarification_keeps_history_and_writes_compatible_transcript(tmp_path):
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Tài khoản nào?"})]),
        ModelResponse(text="[Nguồn](https://example.com)"),
    )
    state = session(tmp_path, provider)
    state.submit("Tweet mới nhất?")
    assert state.transcript["turns"][0]["status"] == "waiting_for_user"
    state.submit("OpenAI")
    assert {"role": "assistant", "content": "Tài khoản nào?"} in provider.messages[1]
    saved = json.loads(next(tmp_path.glob("*.transcript.json")).read_text(encoding="utf-8"))
    assert saved == json.loads(state.export_json())
    assert len(saved["turns"]) == 2
    assert len(saved["prompt_hash"]) == len(saved["tools_hash"]) == 64
    assert saved["turns"][1]["assistant_text"] == "[Nguồn](https://example.com)"


@pytest.mark.parametrize("approved", [True, False])
def test_send_uses_exact_preview_only_after_click_and_never_repeats(tmp_path, monkeypatch, approved):
    calls = []

    def send(**args):
        calls.append(args)
        return {"status": "sent"}

    monkeypatch.setitem(chat.TOOL_FUNCTIONS, "send", send)
    state = session(tmp_path, ScriptedProvider(ModelResponse(tool_calls=[
        ToolCall("send", {"text": "Bản tin chính xác", "confirmed": True}),
    ])))
    state.submit("Gửi bản tin")
    assert calls == []
    assert state.pending_send["text"] == "Bản tin chính xác"
    state.resolve_send(approved)
    state.resolve_send(True)
    assert calls == ([{"text": "Bản tin chính xác", "confirmed": True}] if approved else [])
    assert state.pending_send is None
    assert state.transcript["turns"][-1]["status"] == ("sent" if approved else "cancelled")
    assert len(state.transcript["turns"]) == 2


def test_provider_failure_preserves_tools_and_redacts_all_outputs(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "private-provider-key")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:secret-bot-token")
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("format", {
            "items": [{"title": "private-provider-key", "url": "https://example.com"}],
        })]),
        RuntimeError("429 private-provider-key https://api.telegram.org/bot123456:secret-bot-token/sendMessage"),
    )
    state = session(tmp_path, provider)
    state.submit("Research")
    turn = state.transcript["turns"][0]
    assert turn["status"] == "provider_error"
    assert len(turn["tool_events"]) == 1
    assert "429" in turn["error"]
    output = state.export_json() + capsys.readouterr().out
    assert "private-provider-key" not in output
    assert "123456:secret-bot-token" not in output
    assert "[REDACTED]" in output


def test_sessions_have_independent_history_pending_actions_and_files(tmp_path):
    first = session(tmp_path, ScriptedProvider(ModelResponse(tool_calls=[
        ToolCall("send", {"text": "Private draft"}),
    ])))
    second = session(tmp_path, ScriptedProvider(ModelResponse(text="Second session")))
    first.submit("First request")
    second.submit("Second request")
    assert second.pending_send is None
    assert "Private draft" not in second.export_json()
    assert len(list(tmp_path.glob("*.transcript.json"))) == 2


def test_round_limit_is_recorded_and_history_is_bounded(tmp_path):
    provider = ScriptedProvider(*[ModelResponse(text=f"Answer {i}") for i in range(7)])
    state = session(tmp_path, provider)
    for i in range(7):
        state.submit(f"Question {i}")
    assert len(provider.messages[-1]) == 12  # system + 5 pairs + current request
    assert all(m["content"] != "Question 0" for m in provider.messages[-1])
    looping = ScriptedProvider(*[ModelResponse(tool_calls=[
        ToolCall("format", {"items": []}),
    ]) for _ in range(4)])
    other = session(tmp_path, looping)
    other.submit("Keep researching")
    assert other.transcript["turns"][0]["status"] == "max_tool_rounds"
    assert len(other.transcript["turns"][0]["rounds"]) == 4


def test_disk_error_keeps_downloadable_transcript(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("Disk full")

    monkeypatch.setattr(Path, "write_text", fail)
    state = session(tmp_path, ScriptedProvider(ModelResponse(text="Answer survives")))
    state.submit("Question")
    assert "Disk full" in state.save_error
    assert json.loads(state.export_json())["turns"][0]["assistant_text"] == "Answer survives"


def test_send_error_is_not_retried_and_is_recorded(tmp_path, monkeypatch):
    calls = []

    def fail(**args):
        calls.append(args)
        return {"error": "HTTPError", "message": "Timeout: outcome unknown"}

    monkeypatch.setitem(chat.TOOL_FUNCTIONS, "send", fail)
    state = session(tmp_path, ScriptedProvider(ModelResponse(tool_calls=[ToolCall("send", {"text": "Draft"})])))
    state.submit("Send")
    state.resolve_send(True)
    state.resolve_send(True)
    assert len(calls) == 1
    assert state.transcript["turns"][-1]["status"] == "tool_error"
