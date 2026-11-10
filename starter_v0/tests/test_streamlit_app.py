from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import chat
import ui_session
from providers.base import ModelResponse, ToolCall
from test_ui_session import ScriptedProvider


APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(autouse=True)
def app_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("DAY03_ENV_FILE", str(tmp_path / "no-real-keys.env"))
    monkeypatch.setenv("DAY03_TRANSCRIPTS_DIR", str(tmp_path))
    monkeypatch.setenv("DAY03_UI_PROVIDER", "openrouter")
    monkeypatch.setenv("DAY03_UI_VERSION", "offline-test")
    monkeypatch.delenv("DAY03_UI_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


def start(monkeypatch, provider):
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-key")
    monkeypatch.setattr(ui_session, "make_provider", lambda name: provider)
    return AppTest.from_file(str(APP)).run()


def test_missing_key_keeps_app_open_without_provider_calls():
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.chat_input[0].disabled
    assert any("OPENROUTER_API_KEY" in warning.value for warning in app.warning)


def test_chat_rerun_export_reset_and_session_isolation(monkeypatch):
    provider = ScriptedProvider(ModelResponse(text="[Nguồn](https://example.com)"))
    app = start(monkeypatch, provider)
    app.chat_input[0].set_value("Tìm tin AI").run()
    assert not app.exception
    assert len(app.chat_message) == 2
    assert any("https://example.com" in item.value for item in app.markdown)
    app.run()
    assert len(provider.messages) == 1
    state = app.session_state["chat_session"]
    assert '"user": "Tìm tin AI"' in state.export_json()
    assert len(app.get("download_button")) == 1
    second = AppTest.from_file(str(APP)).run()
    assert len(second.chat_message) == 0
    assert second.session_state["chat_session"].filename != state.filename
    app.button(key="new_chat").click().run()
    assert len(app.chat_message) == 0
    assert app.session_state["chat_session"].filename != state.filename
    assert len(provider.messages) == 1


@pytest.mark.parametrize("approved", [True, False])
def test_confirmation_controls_are_the_only_way_to_send(monkeypatch, approved):
    sends = []

    def send(**args):
        sends.append(args)
        return {"status": "sent"}

    monkeypatch.setitem(chat.TOOL_FUNCTIONS, "send", send)
    app = start(monkeypatch, ScriptedProvider(ModelResponse(tool_calls=[
        ToolCall("send", {"text": "Nội dung xem trước", "confirmed": True}),
    ])))
    app.chat_input[0].set_value("Gửi đi").run()
    assert not app.exception
    assert app.chat_input[0].disabled
    assert sends == []
    assert any("Nội dung xem trước" in item.value for item in app.code)
    app.button(key="confirm_send" if approved else "cancel_send").click().run()
    app.run()
    assert not app.exception
    assert sends == ([{"text": "Nội dung xem trước", "confirmed": True}] if approved else [])
    assert not app.chat_input[0].disabled


def test_provider_error_is_visible_and_redacted(monkeypatch):
    app = start(monkeypatch, ScriptedProvider(RuntimeError("429: offline-key")))
    app.chat_input[0].set_value("Hello").run()
    assert not app.exception
    assert any("429" in item.value for item in app.error)
    assert all("offline-key" not in item.value for item in app.error)


def test_clarify_then_followup_keeps_question_in_context(monkeypatch):
    provider = ScriptedProvider(
        ModelResponse(tool_calls=[ToolCall("clarify", {"question": "Bạn muốn đọc URL nào?"})]),
        ModelResponse(text="Đã nhận URL."),
    )
    app = start(monkeypatch, provider)
    app.chat_input[0].set_value("Đọc bài này").run()
    assert not app.chat_input[0].disabled
    app.chat_input[0].set_value("https://example.com").run()
    assert not app.exception
    assert len(app.chat_message) == 4
    assert {"role": "assistant", "content": "Bạn muốn đọc URL nào?"} in provider.messages[1]


def test_new_chat_discards_pending_send_without_sending(monkeypatch):
    sends = []
    monkeypatch.setitem(chat.TOOL_FUNCTIONS, "send", lambda **args: sends.append(args))
    app = start(monkeypatch, ScriptedProvider(ModelResponse(tool_calls=[
        ToolCall("send", {"text": "Draft from previous session", "confirmed": True}),
    ])))
    app.chat_input[0].set_value("Gửi bản tin").run()
    assert app.session_state["chat_session"].pending_send is not None
    app.button(key="new_chat").click().run()
    assert not app.exception
    assert app.session_state["chat_session"].pending_send is None
    assert not any(button.key in {"confirm_send", "cancel_send"} for button in app.button)
    assert len(app.chat_message) == 0
    assert sends == []
