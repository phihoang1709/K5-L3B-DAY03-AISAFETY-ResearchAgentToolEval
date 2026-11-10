"""Run from the repository root: streamlit run starter_v0/app.py."""
from __future__ import annotations

import os

import streamlit as st

from chat import ROOT
from env_loader import load_lab_env
from ui_session import ChatSession, UISettings, redact


EXAMPLES = [
    "Tìm 3 tin mới về AI trong tuần này, kèm nguồn.",
    "Đọc và tóm tắt bài viết này giúp tôi.",
    "Tìm paper về đánh giá AI agent trên arXiv.",
]


def render_turn(turn: dict) -> None:
    turn = redact(turn)
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        if turn.get("assistant_text"):
            st.markdown(turn["assistant_text"])
        if turn.get("error"):
            st.error(turn["error"])
        if turn["status"] == "max_tool_rounds":
            st.warning("Đã đạt giới hạn xử lý. Có thể thu hẹp yêu cầu rồi thử tiếp.")
        for event in turn.get("tool_events", []):
            result = event.get("result", event)
            if isinstance(result, dict) and result.get("error"):
                st.error(f"Tool {event['tool']}: {result['error']} — {result.get('message', '')}")
        with st.expander(f"Chi tiết lượt {turn['turn_index']} · {len(turn['tool_events'])} lần gọi tool"):
            st.caption(f"Trạng thái: {turn['status']}")
            st.json({"tool_events": turn["tool_events"], "rounds": turn["rounds"]}, expanded=False)

    
def main() -> None:
    st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="centered")
    st.title("🔎 Research Agent")
    st.caption("Tìm thông tin, đọc tài liệu và tổng hợp với nguồn tham khảo.")

    try:
        load_lab_env(ROOT)
        try:
            for name, value in st.secrets.items():
                if isinstance(value, str):
                    os.environ[name] = value
        except FileNotFoundError:
            pass  # Local .env is sufficient; Cloud secrets are optional here.
        settings = UISettings.from_env()
        if "chat_session" not in st.session_state:
            st.session_state.chat_session = ChatSession(settings)
    except Exception as exc:
        st.error(redact(f"Không khởi tạo được ứng dụng: {type(exc).__name__}: {exc}"))
        st.stop()

    state: ChatSession = st.session_state.chat_session
    missing_key = state.settings.missing_key()

    with st.sidebar:
        st.header("Phiên nghiên cứu")
        st.caption("Provider")
        st.write(state.settings.provider)
        st.caption("Model")
        st.write(state.model or "Mặc định của provider")
        st.caption("Version")
        st.write(state.settings.version)
        if st.button("Cuộc trò chuyện mới", key="new_chat", use_container_width=True):
            st.session_state.chat_session = ChatSession(settings)
            st.rerun()
        st.download_button(
            "Tải transcript JSON", data=state.export_json(), file_name=state.filename,
            mime="application/json", disabled=not state.transcript["turns"],
            use_container_width=True, on_click="ignore",
        )
        st.caption("Transcript được lưu sau mỗi lượt. Tải về để giữ bằng chứng demo.")
        with st.expander("Các tool của agent"):
            for tool in state.declarations:
                st.markdown(f"**{tool['name']}** — {tool.get('description', '')}")
        with st.expander("Thông tin phiên"):
            st.caption(state.transcript["artifact_version"])
            st.caption(f"Tối đa {state.settings.max_tool_rounds} vòng tool/lượt · nhớ {state.settings.history_window} cặp hội thoại")

    if missing_key:
        st.warning(f"Chưa cấu hình {missing_key}. Thêm key vào starter_v0/.env hoặc Secrets của Streamlit để bắt đầu chat.")
    if state.save_error:
        st.warning(state.save_error)

    if not state.transcript["turns"]:
        st.subheader("Bạn muốn tìm hiểu điều gì?")
        st.write("Chọn một gợi ý để điền vào ô chat, hoặc nhập yêu cầu của bạn.")
        for index, example in enumerate(EXAMPLES):
            st.button(
                example, key=f"example_{index}", use_container_width=True,
                on_click=lambda text=example: st.session_state.update(chat_prompt=text),
                disabled=bool(missing_key),
            )

    for turn in state.transcript["turns"]:
        render_turn(turn)

    if state.pending_send:
        st.warning("Chờ xác nhận gửi lên Telegram")
        st.caption("Nội dung sẽ được gửi nguyên văn tới channel đã cấu hình của nhóm.")
        st.code(state.pending_send["text"], language=None, wrap_lines=True)
        confirm, cancel = st.columns(2)
        if confirm.button("Xác nhận gửi", key="confirm_send", type="primary", use_container_width=True):
            with st.spinner("Đang gửi nội dung đã xác nhận…"):
                state.resolve_send(True)
            st.rerun()
        if cancel.button("Hủy", key="cancel_send", use_container_width=True):
            state.resolve_send(False)
            st.rerun()

    text = st.chat_input(
        "Nhập câu hỏi hoặc yêu cầu nghiên cứu…", key="chat_prompt",
        disabled=bool(missing_key) or state.pending_send is not None,
    )
    if text:
        with st.spinner("Agent đang đọc yêu cầu và sử dụng tool…"):
            state.submit(text)
        st.rerun()


if __name__ == "__main__":
    main()
