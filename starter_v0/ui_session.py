"""Session-local chat state for the Streamlit UI; no Streamlit or network at import."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote, quote_plus
from uuid import uuid4

from chat import (
    ARTIFACTS_DIR, ROOT, execute_tool_call, json_text, now_iso,
    run_model_tool_loop, safe_slug, trim_history, write_transcript,
)
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from tools.send.tool import send_telegram
from versioning import artifact_version_dict, build_artifact_version


PROVIDER_KEYS = {
    "openrouter": "OPENROUTER_API_KEY", "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "ollama": None,
}
SECRET_NAME = re.compile(r"API_KEY|TOKEN|SECRET|PASSWORD", re.IGNORECASE)


def redact(value: Any) -> Any:
    """Remove configured credentials and common credential forms before UI/export."""
    if isinstance(value, dict):
        return {key: "[REDACTED]" if SECRET_NAME.search(str(key)) else redact(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if not isinstance(value, str):
        return value
    secrets = {secret for name, secret in os.environ.items() if SECRET_NAME.search(name) and secret}
    for secret in sorted(secrets, key=len, reverse=True):
        for variant in {secret, quote(secret, safe=""), quote_plus(secret)}:
            value = value.replace(variant, "[REDACTED]")
    value = re.sub(r"(?i)(bearer\s+)\S+", r"\1[REDACTED]", value)
    value = re.sub(r"bot\d+:[A-Za-z0-9_-]+", "bot[REDACTED]", value)
    return re.sub(r"(?i)([?&](?:api[_-]?key|token|secret|password)=)[^&\s]+", r"\1[REDACTED]", value)


@dataclass(frozen=True)
class UISettings:
    provider: str = "openrouter"
    model: str | None = None
    version: str = "ui"
    history_window: int = 5
    max_tool_rounds: int = 4
    transcripts_dir: Path = ROOT / "transcripts"

    @classmethod
    def from_env(cls) -> UISettings:
        provider = os.getenv("DAY03_UI_PROVIDER", "openrouter").strip().lower()
        if provider not in PROVIDER_KEYS:
            raise ValueError(f"Provider không hỗ trợ: {provider}")
        return cls(
            provider=provider,
            model=os.getenv("DAY03_UI_MODEL", "").strip() or None,
            version=os.getenv("DAY03_UI_VERSION", "ui").strip() or "ui",
            transcripts_dir=Path(os.getenv("DAY03_TRANSCRIPTS_DIR", str(ROOT / "transcripts"))),
        )

    def missing_key(self) -> str | None:
        key = PROVIDER_KEYS[self.provider]
        return key if key and not os.getenv(key, "").strip() else None


class ChatSession:
    def __init__(self, settings: UISettings, *, provider: Any = None) -> None:
        self.settings = settings
        self.provider = provider if provider is not None else make_provider(settings.provider)
        self.model = settings.model or getattr(self.provider, "default_model", None)
        self.declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
        self.tools = to_openai_tools(self.declarations)
        self.system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
        version = build_artifact_version(settings.version, ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")
        self.history: list[dict[str, str]] = []
        self.pending_send: dict[str, Any] | None = None
        self.save_error: str | None = None
        self.transcript: dict[str, Any] = {
            "transcript_id": f"{safe_slug(settings.version)}_{safe_slug(settings.provider)}_{uuid4().hex}",
            **artifact_version_dict(version),
            "provider": settings.provider, "model": self.model,
            "system_prompt": str(ARTIFACTS_DIR / "system_prompt.md"),
            "tools": str(ARTIFACTS_DIR / "tools.yaml"),
            "history_window": settings.history_window, "max_tool_rounds": settings.max_tool_rounds,
            "created_at": now_iso(), "updated_at": now_iso(), "turns": [],
        }

    @property
    def filename(self) -> str:
        return f"{self.transcript['transcript_id']}.transcript.json"

    def export_json(self) -> str:
        return json_text(redact(self.transcript))

    def _save(self) -> None:
        self.transcript["updated_at"] = now_iso()
        try:
            write_transcript(self.settings.transcripts_dir / self.filename, redact(self.transcript))
            self.save_error = None
        except OSError as exc:
            self.save_error = redact(f"Không lưu được transcript: {exc}. Bạn vẫn có thể tải JSON.")

    def _start_turn(self, text: str) -> dict[str, Any]:
        turn = {
            "turn_index": len(self.transcript["turns"]) + 1,
            "started_at": now_iso(), "user": redact(text), "status": "started",
            "assistant_text": "", "rounds": [], "tool_events": [],
        }
        self.transcript["turns"].append(turn)
        return turn

    def _finish_turn(self, turn: dict[str, Any]) -> None:
        turn["ended_at"] = now_iso()
        safe_turn = redact(turn)
        turn.clear()
        turn.update(safe_turn)
        self.history.extend([
            {"role": "user", "content": turn["user"]},
            {"role": "assistant", "content": turn["assistant_text"]},
        ])
        self.history = trim_history(self.history, self.settings.history_window)
        self._save()

    def _execute(self, call: ToolCall) -> dict[str, Any]:
        if call.name == "send" or TOOL_FUNCTIONS.get(call.name) is send_telegram:
            text = call.args.get("text")
            if not isinstance(text, str) or not text.strip() or redact(text) != text:
                return {"tool": call.name, "args": redact(call.args), "result": {
                    "error": "invalid_send_text",
                    "message": "Nội dung gửi phải là văn bản không rỗng và không chứa secrets.",
                }}
            self.pending_send = {
                "tool": call.name, "text": text,
                "request_turn_index": len(self.transcript["turns"]),
            }
            return {"tool": call.name, "args": call.args, "result": {
                "status": "needs_confirmation", "requires_confirmation": True,
                "question": "Kiểm tra nội dung bên dưới rồi chọn Xác nhận gửi hoặc Hủy.",
            }}
        return redact(execute_tool_call(call))

    def submit(self, text: str) -> None:
        if self.pending_send is not None:
            raise ValueError("Hãy xác nhận hoặc hủy bản gửi đang chờ trước.")
        text = text.strip()
        if not text:
            return
        turn = self._start_turn(text)
        try:
            turn.update(run_model_tool_loop(
                provider=self.provider,
                messages=[{"role": "system", "content": self.system_prompt},
                          *self.history, {"role": "user", "content": redact(text)}],
                tools=self.tools, model=self.model, max_tool_rounds=self.settings.max_tool_rounds,
                tool_executor=self._execute, capture_errors=True,
            ))
            if turn["status"] == "max_tool_rounds":
                turn["assistant_text"] = f"Đã dừng sau {self.settings.max_tool_rounds} vòng tool; yêu cầu chưa hoàn tất. Xem chi tiết bên dưới."
        except Exception as exc:
            turn.update(status="provider_error", assistant_text="Không thể hoàn tất yêu cầu.",
                        error=f"{type(exc).__name__}: {exc}")
        self._finish_turn(turn)

    def resolve_send(self, approved: bool) -> None:
        pending = self.pending_send
        if pending is None:
            return
        # Consume before I/O: a rerun or a repeated click must never send twice.
        self.pending_send = None
        turn = self._start_turn("Xác nhận gửi" if approved else "Hủy gửi")
        turn["confirmation"] = {**pending, "approved": approved}
        if not approved:
            turn.update(status="cancelled", assistant_text="Đã hủy. Không gửi nội dung lên Telegram.")
        else:
            self._save()  # Keep the explicit user decision before the external action.
            event = redact(execute_tool_call(ToolCall(pending["tool"], {
                "text": pending["text"], "confirmed": True,
            })))
            turn["tool_events"] = [event]
            result = event.get("result", {})
            if result.get("status") == "sent" and not result.get("error"):
                turn.update(status="sent", assistant_text="Đã gửi nội dung đã xác nhận lên Telegram.")
            else:
                turn.update(status="tool_error", assistant_text="Chưa xác nhận được việc gửi thành công. Kiểm tra Telegram trước khi thử lại.",
                            error=json_text(result))
        self._finish_turn(turn)
